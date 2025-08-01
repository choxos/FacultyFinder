#!/usr/bin/env python3
"""
FacultyFinder - FastAPI Application
High-performance API for academic faculty discovery
"""

import os
import logging
import time
import hashlib
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Path, Request, status, Depends, Cookie, Response, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates

# Database imports
import asyncpg
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# OAuth imports
from webapp.oauth import oauth, oauth_config, oauth_handler, init_oauth_handler, get_oauth_handler

# Professor ID helper functions
def generate_professor_id(university_code: str, sequence_id: int) -> str:
    """Generate professor_id from university_code and sequence_id"""
    return f"{university_code}-{sequence_id:05d}"

def parse_professor_id(professor_id: str) -> tuple:
    """Parse professor_id to extract university_code and sequence_id"""
    # CA-ON-002-00001 → ("CA-ON-002", 1)
    parts = professor_id.split('-')
    if len(parts) >= 4:
        university_code = '-'.join(parts[:-1])  # CA-ON-002
        sequence_id = int(parts[-1])  # 1 (from 00001)
        return university_code, sequence_id
    else:
        raise ValueError(f"Invalid professor_id format: {professor_id}")

def determine_employment_type(full_time: bool, adjunct: bool) -> str:
    """Determine employment type based on full_time and adjunct flags"""
    if adjunct:
        return "adjunct"
    elif full_time:
        return "full-time"
    else:
        return "part-time"

# Load environment variables - prioritize production .env
env_files = ['/var/www/ff/.env', '.env', '.env.test']
for env_file in env_files:
    if os.path.exists(env_file):
        load_dotenv(env_file)
        break

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration - use environment variables directly
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# Global database pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown"""
    global db_pool
    
    # Startup
    logger.info("🚀 Starting FacultyFinder FastAPI application...")
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
        logger.info("✅ Database pool created successfully")
        
        # Test database connection
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM professors")
            logger.info(f"📊 Connected to database with {result} professors")
            
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down FacultyFinder...")
    if db_pool:
        await db_pool.close()
        logger.info("✅ Database pool closed")

# Initialize FastAPI app
app = FastAPI(
    title="FacultyFinder API",
    description="High-performance API for discovering academic faculty and research collaborators worldwide",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "your-secret-key-here"))

# Mount static files
static_dir = "webapp/static" if os.path.exists("webapp/static") else "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize templates
templates = Jinja2Templates(directory="webapp/templates")

# User Model with Granular Admin Permissions
class User:
    def __init__(self, user_data: dict):
        self.id = user_data.get('id')
        self.username = user_data.get('username', '')
        self.email = user_data.get('email', '')
        self.first_name = user_data.get('first_name', '')
        self.last_name = user_data.get('last_name', '')
        self.role = user_data.get('role', 'user')
        self.is_active = user_data.get('is_active', True)
        self.name = user_data.get('name', '')  # OAuth name
        self.picture = user_data.get('picture', '')
        self.is_admin_flag = user_data.get('is_admin', False)  # PostgreSQL
        
        # Admin Permissions
        self.can_manage_ai_requests = user_data.get('can_manage_ai_requests', False)
        self.can_manage_database = user_data.get('can_manage_database', False)
        self.can_manage_users = user_data.get('can_manage_users', False)
        self.is_superuser = user_data.get('is_superuser', False)
        
    @property
    def is_authenticated(self):
        return self.id is not None
    
    def is_admin(self):
        # Check if user has any admin permissions
        return (
            self.role == 'admin' or 
            self.is_admin_flag or 
            self.can_manage_ai_requests or 
            self.can_manage_database or 
            self.can_manage_users or 
            self.is_superuser
        )
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific admin permission"""
        if self.is_superuser:
            return True
            
        permission_map = {
            'ai_requests': self.can_manage_ai_requests,
            'database': self.can_manage_database,
            'users': self.can_manage_users,
            'admin': self.is_admin()
        }
        
        return permission_map.get(permission, False)
    
    def get_admin_permissions(self) -> list:
        """Get list of admin permissions this user has"""
        permissions = []
        if self.is_superuser:
            return ['ai_requests', 'database', 'users', 'superuser']
        
        if self.can_manage_ai_requests:
            permissions.append('ai_requests')
        if self.can_manage_database:
            permissions.append('database')
        if self.can_manage_users:
            permissions.append('users')
            
        return permissions
    
    @property
    def full_name(self):
        if self.name:  # OAuth name
            return self.name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email
    
    def get_full_name(self):
        return self.full_name

# Authentication Dependencies
async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session"""
    user_data = request.session.get('user')
    if user_data:
        return User(user_data)
    return None

async def require_auth(request: Request) -> User:
    """Require authentication - redirect to login if not authenticated"""
    user = await get_current_user(request)
    if not user or not user.is_authenticated:
        raise HTTPException(
            status_code=302,
            detail="Authentication required",
            headers={"Location": "/login"}
        )
    return user

async def require_admin(request: Request) -> User:
    """Require any admin role"""
    user = await require_auth(request)
    if not user.is_admin():
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_ai_requests_permission(request: Request) -> User:
    """Require AI requests management permission"""
    user = await require_auth(request)
    if not user.has_permission('ai_requests'):
        raise HTTPException(status_code=403, detail="AI requests management permission required")
    return user

async def require_database_permission(request: Request) -> User:
    """Require database management permission"""
    user = await require_auth(request)
    if not user.has_permission('database'):
        raise HTTPException(status_code=403, detail="Database management permission required")
    return user

async def require_users_permission(request: Request) -> User:
    """Require user management permission"""
    user = await require_auth(request)
    if not user.has_permission('users'):
        raise HTTPException(status_code=403, detail="User management permission required")
    return user

# Pydantic models
class StatsResponse(BaseModel):
    total_professors: int = Field(..., description="Total number of professors")
    total_universities: int = Field(..., description="Total number of universities")
    total_publications: int = Field(..., description="Total number of publications")
    countries_count: int = Field(..., description="Number of countries")

class University(BaseModel):
    id: int
    name: str
    country: str
    city: Optional[str] = None
    university_code: str
    province: Optional[str] = None
    province_state: Optional[str] = None
    address: Optional[str] = None
    building_number: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    full_address: Optional[str] = None  # Computed field for Google Maps
    website: Optional[str] = None
    type: Optional[str] = None
    language: Optional[str] = None
    established: Optional[int] = None
    faculty_count: int = 0
    department_count: int = 0

class Professor(BaseModel):
    id: int
    professor_id: str  # Computed field - generated from university_code + sequence_id (e.g., "CA-ON-002-00001")
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    university_code: Optional[str] = None
    university_name: Optional[str] = None
    university_address: Optional[str] = None
    university_city: Optional[str] = None
    university_province: Optional[str] = None
    university_country: Optional[str] = None
    university_full_address: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    primary_position: Optional[str] = None
    research_areas: Optional[str] = None
    total_publications: Optional[int] = 0
    publication_count: Optional[int] = 0
    publications_last_5_years: Optional[int] = 0
    citation_count: Optional[int] = 0
    h_index: Optional[int] = 0
    adjunct: Optional[bool] = False
    full_time: Optional[bool] = True  # TRUE = full-time, FALSE = part-time
    employment_type: Optional[str] = None  # Computed: "full-time", "part-time", "adjunct"

class Country(BaseModel):
    country: str
    university_count: int
    faculty_count: int

class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total_count: int
    has_more: bool
    total_pages: int

class UniversitiesResponse(BaseModel):
    universities: List[University]
    pagination: PaginationInfo

class FacultiesResponse(BaseModel):
    faculties: List[Professor]
    pagination: PaginationInfo

# Admin database management models
class UniversityCreate(BaseModel):
    university_code: str
    name: str
    country: str
    province_state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    university_type: Optional[str] = "Public"
    languages: Optional[str] = None
    year_established: Optional[int] = None

class UniversityUpdate(BaseModel):
    university_code: Optional[str] = None
    name: Optional[str] = None
    country: Optional[str] = None
    province_state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    university_type: Optional[str] = None
    languages: Optional[str] = None
    year_established: Optional[int] = None

class ProfessorCreate(BaseModel):
    faculty_id: str
    name: Optional[str] = None
    first_name: str
    last_name: str
    middle_names: Optional[str] = None
    degrees: Optional[str] = None
    research_areas: Optional[str] = None
    university_code: str
    faculty: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    full_time: Optional[bool] = False
    adjunct: Optional[bool] = False
    uni_email: Optional[str] = None
    website: Optional[str] = None
    google_scholar: Optional[str] = None
    orcid: Optional[str] = None
    linkedin: Optional[str] = None

class ProfessorUpdate(BaseModel):
    faculty_id: Optional[str] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_names: Optional[str] = None
    degrees: Optional[str] = None
    research_areas: Optional[str] = None
    university_code: Optional[str] = None
    faculty: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    full_time: Optional[bool] = None
    adjunct: Optional[bool] = None
    uni_email: Optional[str] = None
    website: Optional[str] = None
    google_scholar: Optional[str] = None
    orcid: Optional[str] = None
    linkedin: Optional[str] = None

# Database helper functions
async def get_db_connection():
    """Get database connection from pool"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")
    return db_pool.acquire()

async def get_summary_statistics() -> StatsResponse:
    """Get homepage statistics"""
    async with get_db_connection() as conn:
        # Get counts using DISTINCT to handle any remaining duplicates
        prof_count = await conn.fetchval("SELECT COUNT(DISTINCT name) FROM professors")
        uni_count = await conn.fetchval("SELECT COUNT(DISTINCT name) FROM universities")
        country_count = await conn.fetchval(
            "SELECT COUNT(DISTINCT country) FROM universities WHERE country IS NOT NULL AND country != ''"
        )
        
        # Publications count (might be 0 for now)
        try:
            pub_count = await conn.fetchval("SELECT COUNT(*) FROM publications")
        except:
            pub_count = 0
        
        return StatsResponse(
            total_professors=prof_count,
            total_universities=uni_count,
            total_publications=pub_count,
            countries_count=country_count
        )

async def get_top_universities(limit: int = 8) -> List[University]:
    """Get top universities by faculty count"""
    async with get_db_connection() as conn:
        query = """
            SELECT u.id, u.name, u.country, u.city, u.university_code, COALESCE(u.province_state, '') as province, u.year_established,
                   COUNT(p.id) as faculty_count
            FROM universities u
            LEFT JOIN professors p ON p.university_code = u.university_code
            WHERE u.name IS NOT NULL
            GROUP BY u.id, u.name, u.country, u.city, u.university_code, u.province_state, u.year_established
            HAVING COUNT(p.id) > 0
            ORDER BY COUNT(p.id) DESC
            LIMIT $1
        """
        
        rows = await conn.fetch(query, limit)
        return [University(**dict(row)) for row in rows]

# Routes

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Serve the homepage"""
    try:
        with open("webapp/static/index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        # Fallback simple HTML if static file doesn't exist
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FacultyFinder</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1 class="text-center">🎓 FacultyFinder</h1>
                <p class="text-center lead">Discover academic faculty worldwide</p>
                <div class="text-center mt-4">
                    <a href="/api/docs" class="btn btn-primary">API Documentation</a>
                    <a href="/api/v1/stats" class="btn btn-success">View Stats</a>
                </div>
            </div>
        </body>
        </html>
        """)

@app.get("/universities", response_class=HTMLResponse)
async def universities_page(request: Request):
    """Serve the universities page"""
    try:
        with open("webapp/static/universities.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Universities - FacultyFinder</title></head>
        <body>
            <h1>Universities</h1>
            <p>API: <a href="/api/v1/universities">/api/v1/universities</a></p>
        </body>
        </html>
        """)

@app.get("/faculties", response_class=HTMLResponse)
async def faculties_page(request: Request):
    """Serve the faculties page"""
    try:
        with open("webapp/static/faculties.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Faculties - FacultyFinder</title></head>
        <body>
            <h1>Faculties</h1>
            <p>API: <a href="/api/v1/faculties">/api/v1/faculties</a></p>
        </body>
        </html>
        """)

@app.get("/countries", response_class=HTMLResponse)
async def countries_page(request: Request):
    """Serve the countries page"""
    try:
        with open("webapp/static/countries.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Countries - FacultyFinder</title></head>
        <body>
            <h1>Countries</h1>
            <p>API: <a href="/api/v1/countries">/api/v1/countries</a></p>
        </body>
        </html>
        """)

@app.get("/ai-assistant", response_class=HTMLResponse)
async def ai_assistant_page(request: Request):
    """Serve the AI assistant page"""
    try:
        with open("webapp/static/ai-assistant.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>AI Assistant - FacultyFinder</title></head>
        <body>
            <h1>AI Assistant</h1>
            <p>Pricing: Expert review $99-$999, Unlimited AI $49/month</p>
        </body>
        </html>
        """)

# API Routes

@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats(request: Request):
    """Get summary statistics"""
    try:
        return await get_summary_statistics()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.get("/api/v1/universities", response_model=UniversitiesResponse)
async def get_universities(
    request: Request,
    search: Optional[str] = Query(None, description="Search term for university name or location"),
    country: Optional[str] = Query(None, description="Filter by country"),
    province: Optional[str] = Query(None, description="Filter by province/state"),
    university_type: Optional[str] = Query(None, description="Filter by university type"),
    sort_by: str = Query("faculty_count", description="Sort by: faculty_count, name, location, year_established"),
    sort_direction: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get universities with filtering and pagination"""
    try:
        async with get_db_connection() as conn:
            # Build WHERE clause
            where_conditions = []
            params = []
            param_count = 0
            
            if search:
                param_count += 1
                where_conditions.append(f"(u.name ILIKE ${param_count} OR u.city ILIKE ${param_count})")
                params.append(f"%{search}%")
            
            if country:
                param_count += 1
                where_conditions.append(f"u.country = ${param_count}")
                params.append(country)
            
            if province:
                param_count += 1
                where_conditions.append(f"u.province_state = ${param_count}")
                params.append(province)
            
            if university_type:
                param_count += 1
                where_conditions.append(f"u.type = ${param_count}")
                params.append(university_type)
            
            # Ensure there's always a WHERE condition
            if not where_conditions:
                where_conditions = ["1=1"]
            
            # Build ORDER BY clause
            direction = "DESC" if sort_direction.lower() == "desc" else "ASC"
            order_mapping = {
                "faculty_count": f"faculty_count {direction}",
                "name": f"u.name {direction}",
                "location": f"u.country {direction}, u.city {direction}",
                "established": f"u.year_established {direction} NULLS LAST"
            }
            order_clause = order_mapping.get(sort_by, f"faculty_count {direction}")
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Main query
            query = f"""
                SELECT u.id, u.name, u.country, u.city, u.university_code, 
                       COALESCE(u.province_state, '') as province_state,
                       COALESCE(u.address, '') as address,
                       COALESCE(u.building_number, '') as building_number,
                       COALESCE(u.street, '') as street,
                       COALESCE(u.postal_code, '') as postal_code,
                       CASE 
                           WHEN u.building_number IS NOT NULL AND u.street IS NOT NULL THEN
                               CONCAT_WS(', ',
                                   u.name,
                                   NULLIF(CONCAT_WS(' ', u.building_number, u.street), ''),
                                   u.city,
                                   NULLIF(CONCAT_WS(' ', u.province_state, u.postal_code), ''),
                                   u.country
                               )
                           ELSE CONCAT_WS(', ', u.name, u.city, u.province_state, u.country)
                       END as full_address,
                       COALESCE(u.website, '') as website,
                       COALESCE(u.university_type, '') as type,
                       COALESCE(u.languages, '') as language,
                       u.year_established as established,
                       COUNT(p.id) as faculty_count,
                       COUNT(DISTINCT COALESCE(p.department, 'Unknown')) as department_count
                FROM universities u
                LEFT JOIN professors p ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
                GROUP BY u.id, u.name, u.country, u.city, u.university_code, u.province_state,
                         u.address, u.building_number, u.street, u.postal_code, u.website, 
                         u.university_type, u.languages, u.year_established
                HAVING COUNT(p.id) >= 0
                ORDER BY {order_clause}
                LIMIT {per_page + 1} OFFSET {offset}
            """
            
            rows = await conn.fetch(query, *params)
            
            # Check if there are more results
            has_more = len(rows) > per_page
            if has_more:
                rows = rows[:per_page]
            
            universities = [University(**dict(row)) for row in rows]
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(*)
                FROM (
                    SELECT DISTINCT u.id
                    FROM universities u
                    LEFT JOIN professors p ON p.university_code = u.university_code
                    WHERE {' AND '.join(where_conditions)}
                    GROUP BY u.id
                    HAVING COUNT(p.id) >= 0
                ) subquery
            """
            
            count_rows = await conn.fetch(count_query, *params)
            total_count = len(count_rows)
            
            pagination = PaginationInfo(
                page=page,
                per_page=per_page,
                total_count=total_count,
                has_more=has_more,
                total_pages=(total_count + per_page - 1) // per_page
            )
            
            return UniversitiesResponse(universities=universities, pagination=pagination)
            
    except Exception as e:
        logger.error(f"Error getting universities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve universities")

@app.get("/api/v1/faculties", response_model=FacultiesResponse)
async def get_faculties(
    request: Request,
    search: Optional[str] = Query(None, description="Search term for professor name or research areas"),
    university: Optional[str] = Query(None, description="Filter by university code"),
    department: Optional[str] = Query(None, description="Filter by department"),
    research_area: Optional[str] = Query(None, description="Filter by research area"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type (full-time, part-time, adjunct)"),
    sort_by: str = Query("name", description="Sort by: name, university, department, research_areas, publications, recent_publications"),
    sort_direction: str = Query("asc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get faculty with filtering and pagination"""
    try:
        async with get_db_connection() as conn:
            # Build WHERE clause
            where_conditions = ["p.name IS NOT NULL"]
            params = []
            param_count = 0
            
            if search:
                param_count += 2
                where_conditions.append(f"(p.name ILIKE ${param_count-1} OR p.research_areas ILIKE ${param_count})")
                params.extend([f"%{search}%", f"%{search}%"])
            
            if university:
                param_count += 1
                where_conditions.append(f"p.university_code = ${param_count}")
                params.append(university)
            
            if department:
                param_count += 1
                where_conditions.append(f"p.department ILIKE ${param_count}")
                params.append(f"%{department}%")
            
            if research_area:
                param_count += 1
                where_conditions.append(f"p.research_areas ILIKE ${param_count}")
                params.append(f"%{research_area}%")
            
            if employment_type:
                param_count += 1
                where_conditions.append(f"p.position ILIKE ${param_count}")
                params.append(f"%{employment_type}%")
            
            # Build ORDER BY clause
            direction = "DESC" if sort_direction.lower() == "desc" else "ASC"
            order_mapping = {
                "name": f"p.name {direction}",
                "university": f"u.name {direction}",
                "department": f"p.department {direction}",
                "research_areas": f"p.research_areas {direction}",
                "publications": f"CAST(0 AS INTEGER) {direction} NULLS LAST",
                "recent_publications": f"CAST(0 AS INTEGER) {direction} NULLS LAST"
            }
            order_clause = order_mapping.get(sort_by, f"p.name {direction}")
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Main query
            query = f"""
                SELECT p.id, p.professor_id as sequence_id, p.name, COALESCE(p.uni_email, p.other_email, '') as email, p.university_code,
                       COALESCE(p.department, '') as department, 
                       COALESCE(p.position, '') as position, 
                       COALESCE(CAST(p.research_areas AS TEXT), '') as research_areas, 
                       0 as publication_count,
                       0 as total_publications,
                       0 as publications_last_5_years,
                       0 as citation_count,
                       0 as h_index,
                       COALESCE(p.adjunct, false) as adjunct,
                       COALESCE(p.full_time, true) as full_time,
                       COALESCE(u.name, '') as university_name,
                       COALESCE(u.address, '') as university_address,
                       COALESCE(u.city, '') as university_city,
                       COALESCE(u.province_state, '') as university_province,
                       COALESCE(u.country, '') as university_country,
                       CASE 
                           WHEN u.building_number IS NOT NULL AND u.street IS NOT NULL THEN
                               CONCAT_WS(', ',
                                   u.name,
                                   NULLIF(CONCAT_WS(' ', u.building_number, u.street), ''),
                                   u.city,
                                   NULLIF(CONCAT_WS(' ', u.province_state, u.postal_code), ''),
                                   u.country
                               )
                           ELSE CONCAT_WS(', ', u.name, u.city, u.province_state, u.country)
                       END as university_full_address
                FROM professors p
                LEFT JOIN universities u ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
                ORDER BY {order_clause}
                LIMIT {per_page + 1} OFFSET {offset}
            """
            
            rows = await conn.fetch(query, *params)
            
            # Check if there are more results
            has_more = len(rows) > per_page
            if has_more:
                rows = rows[:per_page]
            
            # Convert to Professor objects with computed fields
            faculties = []
            for row in rows:
                professor_data = dict(row)
                professor_data['professor_id'] = generate_professor_id(
                    professor_data['university_code'], 
                    professor_data['sequence_id']
                )
                professor_data['employment_type'] = determine_employment_type(
                    professor_data.get('full_time', True),
                    professor_data.get('adjunct', False)
                )
                faculties.append(Professor(**professor_data))
            
            # Get total count
            count_query = f"""
                SELECT COUNT(DISTINCT p.id)
                FROM professors p
                LEFT JOIN universities u ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
            """
            
            total_count = await conn.fetchval(count_query, *params)
            
            pagination = PaginationInfo(
                page=page,
                per_page=per_page,
                total_count=total_count,
                has_more=has_more,
                total_pages=(total_count + per_page - 1) // per_page
            )
            
            return FacultiesResponse(faculties=faculties, pagination=pagination)
            
    except Exception as e:
        logger.error(f"Error getting faculties: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve faculties")

@app.get("/api/v1/countries", response_model=List[Country])
async def get_countries(request: Request):
    """Get countries with university and faculty counts"""
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT u.country, 
                       COUNT(DISTINCT u.id) as university_count,
                       COUNT(DISTINCT p.id) as faculty_count
                FROM universities u
                LEFT JOIN professors p ON p.university_code = u.university_code
                WHERE u.country IS NOT NULL AND u.country != ''
                GROUP BY u.country
                HAVING COUNT(DISTINCT p.id) > 0
                ORDER BY COUNT(DISTINCT p.id) DESC
            """
            
            rows = await conn.fetch(query)
            return [Country(**dict(row)) for row in rows]
            
    except Exception as e:
        logger.error(f"Error getting countries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve countries")

@app.get("/api/v1/professor/{professor_id}")
async def get_professor(request: Request, professor_id: str = Path(..., description="Professor ID (e.g., CA-ON-002-00001) or sequence number")):
    """Get individual professor details"""
    try:
        async with get_db_connection() as conn:
            # Parse professor_id to get university_code and sequence_id
            try:
                university_code, sequence_id = parse_professor_id(professor_id)
                # Use university_code + sequence_id for lookup
                query = """
                    SELECT p.id, p.professor_id as sequence_id, p.name, COALESCE(p.uni_email, p.other_email, '') as email,
                           p.university_code, COALESCE(p.department, '') as department, 
                           COALESCE(p.position, '') as position, 
                           COALESCE(CAST(p.research_areas AS TEXT), '') as research_areas,
                           0 as publication_count, 0 as citation_count, 0 as h_index,
                           COALESCE(p.adjunct, false) as adjunct,
                           COALESCE(p.full_time, true) as full_time,
                           COALESCE(u.name, '') as university_name, 
                           COALESCE(u.city, '') as city, 
                           COALESCE(u.province_state, '') as province_state, 
                           COALESCE(u.country, '') as country
                    FROM professors p
                    LEFT JOIN universities u ON p.university_code = u.university_code
                    WHERE p.university_code = $1 AND p.professor_id = $2
                """
                row = await conn.fetchrow(query, university_code, sequence_id)
            except ValueError:
                # Fallback: treat as direct sequence_id if parsing fails
                if professor_id.isdigit():
                    query = """
                        SELECT p.id, p.professor_id as sequence_id, p.name, COALESCE(p.uni_email, p.other_email, '') as email,
                               p.university_code, COALESCE(p.department, '') as department, 
                               COALESCE(p.position, '') as position, 
                               COALESCE(CAST(p.research_areas AS TEXT), '') as research_areas,
                               0 as publication_count, 0 as citation_count, 0 as h_index,
                               COALESCE(p.adjunct, false) as adjunct,
                               COALESCE(p.full_time, true) as full_time,
                               COALESCE(u.name, '') as university_name, 
                               COALESCE(u.city, '') as city, 
                               COALESCE(u.province_state, '') as province_state, 
                               COALESCE(u.country, '') as country
                        FROM professors p
                        LEFT JOIN universities u ON p.university_code = u.university_code
                        WHERE p.professor_id = $1
                    """
                    row = await conn.fetchrow(query, int(professor_id))
                else:
                    raise HTTPException(status_code=400, detail="Invalid professor_id format")
            
            if not row:
                raise HTTPException(status_code=404, detail="Professor not found")
            
            # Convert to dict and add computed fields
            professor_data = dict(row)
            professor_data['professor_id'] = generate_professor_id(
                professor_data['university_code'], 
                professor_data['sequence_id']
            )
            professor_data['employment_type'] = determine_employment_type(
                professor_data.get('full_time', True),
                professor_data.get('adjunct', False)
            )
            
            return Professor(**professor_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting professor {professor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Professor detail route
@app.get("/professor/{professor_id}")
async def get_professor_page(request: Request, professor_id: str):
    """Serve professor detail page"""
    return FileResponse(os.path.join(static_dir, "professor.html"))

# University API endpoint
@app.get("/api/v1/university/{university_code}", response_model=University)
async def get_university_by_code(request: Request, university_code: str):
    """Get university details by university code"""
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT u.id, u.name, u.country, u.city, u.university_code, 
                       COALESCE(u.province_state, '') as province, u.year_established,
                       COALESCE(u.website, '') as website, COALESCE(u.university_type, 'Public') as university_type,
                       COUNT(p.id) as faculty_count
                FROM universities u
                LEFT JOIN professors p ON p.university_code = u.university_code
                WHERE u.university_code = $1 OR u.name = $1
                GROUP BY u.id, u.name, u.country, u.city, u.university_code, u.province_state, 
                         u.year_established, u.website, u.university_type
                LIMIT 1
            """
            
            row = await conn.fetchrow(query, university_code)
            
            if not row:
                raise HTTPException(status_code=404, detail="University not found")
            
            # Convert row to dict and ensure all required fields are present
            university_data = dict(row)
            
            # Ensure required fields for University model
            if 'province' not in university_data:
                university_data['province'] = university_data.get('province_state', '')
            
            return University(**university_data)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting university: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve university")

# University profile page route
@app.get("/university/{university_code}")
async def get_university_page(request: Request, university_code: str):
    """Serve university profile page"""
    return FileResponse(os.path.join(static_dir, "university.html"))

# Authentication routes
@app.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    """Serve login page"""
    current_user = await get_current_user(request)
    if current_user and current_user.is_authenticated:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return FileResponse(os.path.join(static_dir, "login.html"))

@app.post("/login")
async def login_user(
    request: Request,
    username_or_email: str = Form(...),
    password: str = Form(...),
    remember: Optional[str] = Form(None)
):
    """Handle user login"""
    try:
        # Find user by username or email using PostgreSQL
        async with get_db_connection() as conn:
            user_data = await conn.fetchrow("""
                SELECT * FROM users 
                WHERE (username = $1 OR email = $1) AND is_active = TRUE
            """, username_or_email)
        
        if not user_data:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid username/email or password"}
            )
        
        # Verify password (using simple SHA256 for now - should use bcrypt in production)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user_data['password_hash'] != password_hash:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid username/email or password"}
            )
        
        # Update last login
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
                WHERE id = $1
            """, user_data['id'])
        
        # Store user in session
        request.session['user'] = dict(user_data)
        
        # Return JSON response for AJAX login
        user = User(dict(user_data))
        if user.is_admin():
            return JSONResponse(
                status_code=200,
                content={"success": True, "redirect": "/admin/dashboard"}
            )
        else:
            return JSONResponse(
                status_code=200,
                content={"success": True, "redirect": "/dashboard"}
            )
                
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Login failed. Please try again."}
        )

@app.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    """Serve registration page"""
    current_user = await get_current_user(request)
    if current_user and current_user.is_authenticated:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return FileResponse(os.path.join(static_dir, "register.html"))

@app.post("/register")
async def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    firstName: str = Form(...),
    lastName: str = Form(...),
    confirmPassword: str = Form(...),
    terms: Optional[str] = Form(None),
    institution: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    newsletter: Optional[str] = Form(None)
):
    """Handle user registration"""
    try:
        # Validate password confirmation
        if password != confirmPassword:
            return JSONResponse(
                status_code=400,
                content={"error": "Passwords do not match"}
            )
        
        # Check if terms are accepted
        if not terms:
            return JSONResponse(
                status_code=400,
                content={"error": "You must accept the terms of service"}
            )
        
        # Check if user already exists
        async with get_db_connection() as conn:
            existing_user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1", email
            )
            
            if existing_user:
                return JSONResponse(
                    status_code=400,
                    content={"error": "An account with this email already exists"}
                )
            
            # Create password hash
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Insert new user
            user = await conn.fetchrow("""
                INSERT INTO users (
                    username, email, password_hash, first_name, last_name,
                    is_active, email_verified
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            """, 
            email,  # Use email as username for now
            email,
            password_hash,
            firstName,
            lastName,
            True,
            False  # Email verification needed
            )
            
            # Store user in session
            request.session['user'] = dict(user)
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "redirect": "/dashboard"}
            )
                
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Registration failed. Please try again."}
        )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(require_auth)):
    """User dashboard"""
    return templates.TemplateResponse("user/dashboard.html", {
        "request": request,
        "current_user": user
    })

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, user: User = Depends(require_auth)):
    """User profile page"""
    return templates.TemplateResponse("user/profile.html", {
        "request": request,
        "current_user": user
    })

# OAuth routes
@app.get("/auth/{provider}")
async def oauth_login(request: Request, provider: str):
    """Initiate OAuth login for specified provider (google or linkedin)"""
    try:
        if provider not in ['google', 'linkedin']:
            raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
        
        if provider == 'google' and not oauth_config.google_configured:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        elif provider == 'linkedin' and not oauth_config.linkedin_configured:
            raise HTTPException(status_code=500, detail="LinkedIn OAuth not configured")
        
        oauth_handler = get_oauth_handler()
        return await oauth_handler.get_authorization_url(request, provider)
        
    except Exception as e:
        logger.error(f"{provider.title()} OAuth initiation error: {e}")
        return RedirectResponse(url=f"/login?error=oauth_failed&provider={provider}")

@app.get("/auth/{provider}/callback")
async def oauth_callback(request: Request, provider: str):
    """Handle OAuth callback from specified provider"""
    try:
        if provider not in ['google', 'linkedin']:
            raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
        
        oauth_handler = get_oauth_handler()
        auth_result = await oauth_handler.handle_callback(request, provider)
        
        # Store user info in session
        request.session['user'] = auth_result['user']
        request.session['access_token'] = auth_result['access_token']
        request.session['provider'] = provider
        
        # Redirect to dashboard or homepage
        return RedirectResponse(url="/?welcome=true")
        
    except Exception as e:
        logger.error(f"{provider.title()} OAuth callback error: {e}")
        return RedirectResponse(url=f"/login?error=auth_failed&provider={provider}")

@app.get("/auth/logout")
async def logout(request: Request):
    """Logout user and clear session"""
    request.session.clear()
    return RedirectResponse(url="/login?logout=true", status_code=302)

@app.get("/logout")
async def logout_alias(request: Request):
    """Logout alias for convenience"""
    return await logout(request)

@app.get("/auth/user")
async def get_current_user_endpoint(request: Request):
    """Get current authenticated user info"""
    user = await get_current_user(request)
    if not user or not user.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Return user data as dictionary instead of User object
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_admin": user.is_admin(),
        "permissions": user.get_admin_permissions()
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    try:
        async with get_db_connection() as conn:
            await conn.fetchval("SELECT 1")
            return {"status": "healthy", "database": "connected", "framework": "FastAPI"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found", "status_code": 404}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500}
    )

# Admin routes
@app.get("/admin", response_class=HTMLResponse)
async def admin_redirect(request: Request):
    """Redirect /admin to /admin/dashboard"""
    return RedirectResponse(url="/admin/dashboard", status_code=302)

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user: User = Depends(require_admin)):
    """Admin dashboard"""
    try:
        # Get dashboard statistics using PostgreSQL
        try:
            async with get_db_connection() as conn:
                users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
                professors_count = await conn.fetchval("SELECT COUNT(*) FROM professors")
                universities_count = await conn.fetchval("SELECT COUNT(*) FROM universities")
                
                database_stats = {
                    "users": {"count": users_count or 0},
                    "professors": {"count": professors_count or 0},
                    "universities": {"count": universities_count or 0},
                    "user_search_history": {"count": 0}  # Placeholder
                }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            database_stats = {
                "users": {"count": 0},
                "professors": {"count": 0},
                "universities": {"count": 0},
                "user_search_history": {"count": 0}
            }
            
            # Get recent notifications (mock for now)
            notifications = []
            
            # System stats (mock for now)
            system_stats = {
                "cpu_percent": 25.3,
                "memory": {"percent": 42.1},
                "disk": {"percent": 67.8},
                "uptime": {"days": 5}
            }
            
            stats = {
                "database": database_stats,
                "system": system_stats,
                "revenue": None,  # Not implemented yet
                "users": None     # Not implemented yet
            }
            
        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "current_user": user,
            "stats": stats,
            "notifications": notifications
        })
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load admin dashboard")

@app.get("/admin/ai-requests", response_class=HTMLResponse)
async def admin_ai_requests(request: Request, user: User = Depends(require_ai_requests_permission)):
    """Admin AI requests management page"""
    return templates.TemplateResponse("admin/ai_requests.html", {
        "request": request,
        "current_user": user
    })

@app.get("/admin/database", response_class=HTMLResponse)
async def admin_database(request: Request, user: User = Depends(require_database_permission)):
    """Admin database management page"""
    return templates.TemplateResponse("admin/database.html", {
        "request": request,
        "current_user": user
    })

@app.get("/api/v1/admin/ai-requests")
async def admin_get_ai_requests(
    request: Request,
    user: User = Depends(require_ai_requests_permission),
    status: Optional[str] = None,
    service_type: Optional[str] = None,
    provider: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get AI requests for admin management"""
    try:
        async with get_db_connection() as conn:
            # Base query combining ai_sessions, user_payments, and crypto_payments
            where_conditions = []
            params = []
            param_count = 0
            
            base_query = """
            SELECT DISTINCT
                ai.id as ai_session_id,
                ai.session_id,
                ai.user_ip,
                ai.ai_provider,
                ai.payment_status as ai_payment_status,
                ai.created_at as session_created_at,
                ai.updated_at as session_updated_at,
                
                -- Regular payments
                up.id as payment_id,
                up.amount as payment_amount,
                up.currency as payment_currency,
                up.service_type as payment_service_type,
                up.service_details as payment_service_details,
                up.status as payment_status,
                up.completed_at as payment_completed_at,
                up.payment_method as payment_method,
                
                -- Crypto payments
                cp.id as crypto_payment_id,
                cp.amount_requested as crypto_amount,
                cp.fiat_amount as crypto_fiat_amount,
                cp.status as crypto_status,
                cp.service_type as crypto_service_type,
                cp.completed_at as crypto_completed_at,
                cc.symbol as crypto_currency,
                cpp.display_name as crypto_provider,
                
                -- User info (if available)
                u.email as user_email,
                u.first_name,
                u.last_name
                
            FROM ai_sessions ai
            LEFT JOIN user_payments up ON ai.payment_session_id = up.payment_intent_id
            LEFT JOIN crypto_payments cp ON ai.payment_session_id = cp.payment_id
            LEFT JOIN crypto_currencies cc ON cp.currency_id = cc.id
            LEFT JOIN crypto_payment_providers cpp ON cp.provider_id = cpp.id
            LEFT JOIN users u ON (up.user_id = u.id OR cp.user_id = u.id)
            """
            
            # Add filters
            if status:
                where_conditions.append(f"(ai.payment_status = ${len(params)+1} OR up.status = ${len(params)+1} OR cp.status = ${len(params)+1})")
                params.append(status)
            
            if service_type:
                where_conditions.append(f"(up.service_type = ${len(params)+1} OR cp.service_type = ${len(params)+1})")
                params.append(service_type)
            
            if provider:
                where_conditions.append(f"(ai.ai_provider = ${len(params)+1} OR cpp.name = ${len(params)+1})")
                params.append(provider)
                
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            base_query += f" ORDER BY ai.created_at DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
            params.extend([limit, offset])
            
            requests = await conn.fetch(base_query, *params)
            
            # Count total for pagination
            count_query = """
            SELECT COUNT(DISTINCT ai.id)
            FROM ai_sessions ai
            LEFT JOIN user_payments up ON ai.payment_session_id = up.payment_intent_id
            LEFT JOIN crypto_payments cp ON ai.payment_session_id = cp.payment_id
            LEFT JOIN crypto_currencies cc ON cp.currency_id = cc.id
            LEFT JOIN crypto_payment_providers cpp ON cp.provider_id = cpp.id
            LEFT JOIN users u ON (up.user_id = u.id OR cp.user_id = u.id)
            """
            
            if where_conditions:
                count_query += " WHERE " + " AND ".join(where_conditions)
            
            total_count = await conn.fetchval(count_query, *params[:-2])  # Exclude limit and offset
            
            # Format results
            results = []
            for req in requests:
                # Determine primary payment info
                payment_info = {}
                if req['payment_id']:
                    payment_info = {
                        'type': 'regular',
                        'amount': req['payment_amount'],
                        'currency': req['payment_currency'],
                        'status': req['payment_status'],
                        'method': req['payment_method'],
                        'service_type': req['payment_service_type'],
                        'completed_at': req['payment_completed_at'].isoformat() if req['payment_completed_at'] else None
                    }
                elif req['crypto_payment_id']:
                    payment_info = {
                        'type': 'crypto',
                        'amount': float(req['crypto_amount']) if req['crypto_amount'] else None,
                        'fiat_amount': req['crypto_fiat_amount'],
                        'currency': req['crypto_currency'],
                        'status': req['crypto_status'],
                        'provider': req['crypto_provider'],
                        'service_type': req['crypto_service_type'],
                        'completed_at': req['crypto_completed_at'].isoformat() if req['crypto_completed_at'] else None
                    }
                
                user_info = {
                    'email': req['user_email'],
                    'name': f"{req['first_name'] or ''} {req['last_name'] or ''}".strip() or 'Anonymous'
                }
                
                results.append({
                    'id': req['ai_session_id'],
                    'session_id': req['session_id'],
                    'user_ip': req['user_ip'],
                    'ai_provider': req['ai_provider'],
                    'ai_payment_status': req['ai_payment_status'],
                    'created_at': req['session_created_at'].isoformat(),
                    'updated_at': req['session_updated_at'].isoformat() if req['session_updated_at'] else None,
                    'user': user_info,
                    'payment': payment_info
                })
            
            return {
                "requests": results,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
            
    except Exception as e:
        logger.error(f"Error fetching AI requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch AI requests")

@app.post("/api/v1/admin/ai-requests/{request_id}/update-status")
async def admin_update_request_status(request: Request, request_id: int, status: str, user: User = Depends(require_ai_requests_permission)):
    """Update AI request status"""
    try:
        async with get_db_connection() as conn:
            # Update ai_sessions status
            await conn.execute(
                "UPDATE ai_sessions SET payment_status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                status, request_id
            )
            
            return {"success": True, "message": f"Request {request_id} status updated to {status}"}
            
    except Exception as e:
        logger.error(f"Error updating request status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update request status")

@app.get("/api/v1/admin/ai-requests/stats")
async def admin_ai_requests_stats(request: Request, user: User = Depends(require_ai_requests_permission)):
    """Get AI requests statistics for admin dashboard"""
    try:
        async with get_db_connection() as conn:
            # Get overall stats
            stats = {}
            
            # Total AI sessions
            stats['total_sessions'] = await conn.fetchval("SELECT COUNT(*) FROM ai_sessions")
            
            # Sessions by status
            session_statuses = await conn.fetch("""
                SELECT payment_status, COUNT(*) as count 
                FROM ai_sessions 
                WHERE payment_status IS NOT NULL 
                GROUP BY payment_status
            """)
            stats['by_status'] = {row['payment_status']: row['count'] for row in session_statuses}
            
            # Sessions by AI provider
            ai_providers = await conn.fetch("""
                SELECT ai_provider, COUNT(*) as count 
                FROM ai_sessions 
                WHERE ai_provider IS NOT NULL 
                GROUP BY ai_provider
            """)
            stats['by_ai_provider'] = {row['ai_provider']: row['count'] for row in ai_providers}
            
            # Revenue stats (combining regular and crypto payments)
            regular_revenue = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0) FROM user_payments 
                WHERE status = 'completed' AND service_type IN ('ai_analysis', 'manual_review')
            """) or 0
            
            crypto_revenue = await conn.fetchval("""
                SELECT COALESCE(SUM(fiat_amount), 0) FROM crypto_payments 
                WHERE status = 'completed' AND service_type IN ('ai_analysis', 'manual_review')
            """) or 0
            
            stats['revenue'] = {
                'total_cents': regular_revenue + crypto_revenue,
                'total_cad': round((regular_revenue + crypto_revenue) / 100, 2),
                'regular_cad': round(regular_revenue / 100, 2),
                'crypto_cad': round(crypto_revenue / 100, 2)
            }
            
            # Recent activity (last 30 days)
            recent_sessions = await conn.fetchval("""
                SELECT COUNT(*) FROM ai_sessions 
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
            """) or 0
            
            stats['recent_activity'] = {
                'sessions_last_30_days': recent_sessions
            }
            
            return stats
            
    except Exception as e:
        logger.error(f"Error fetching AI requests stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch AI requests stats")

# Database Management API Routes
@app.get("/api/v1/admin/universities")
async def admin_get_universities(
    request: Request,
    user: User = Depends(require_database_permission),
    country: Optional[str] = None,
    province_state: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get universities for admin management"""
    try:
        async with get_db_connection() as conn:
            where_conditions = []
            params = []
            
            base_query = """
            SELECT 
                id, university_code, name, country, province_state, city, 
                address, website, university_type, languages, year_established,
                created_at, updated_at
            FROM universities
            """
            
            # Add filters
            if country:
                where_conditions.append(f"country ILIKE ${len(params)+1}")
                params.append(f"%{country}%")
            
            if province_state:
                where_conditions.append(f"province_state ILIKE ${len(params)+1}")
                params.append(f"%{province_state}%")
            
            if search:
                where_conditions.append(f"(name ILIKE ${len(params)+1} OR university_code ILIKE ${len(params)+1})")
                params.append(f"%{search}%")
                
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            base_query += f" ORDER BY name LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
            params.extend([limit, offset])
            
            universities = await conn.fetch(base_query, *params)
            
            # Count total
            count_query = "SELECT COUNT(*) FROM universities"
            if where_conditions:
                count_query += " WHERE " + " AND ".join(where_conditions)
            
            total_count = await conn.fetchval(count_query, *params[:-2])
            
            return {
                "universities": [dict(u) for u in universities],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
            
    except Exception as e:
        logger.error(f"Error fetching universities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch universities")

@app.post("/api/v1/admin/universities")
async def admin_create_university(request: Request, university_data: UniversityCreate, user: User = Depends(require_database_permission)):
    """Create new university"""
    try:
        async with get_db_connection() as conn:
            query = """
            INSERT INTO universities 
            (university_code, name, country, province_state, city, address, website, 
             university_type, languages, year_established)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
            """
            
            result = await conn.fetchrow(
                query,
                university_data.university_code,
                university_data.name,
                university_data.country,
                university_data.province_state,
                university_data.city,
                university_data.address,
                university_data.website,
                university_data.university_type,
                university_data.languages,
                university_data.year_established
            )
            
            return {"success": True, "university": dict(result)}
            
    except Exception as e:
        logger.error(f"Error creating university: {e}")
        raise HTTPException(status_code=500, detail="Failed to create university")

@app.put("/api/v1/admin/universities/{university_id}")
async def admin_update_university(request: Request, university_id: int, university_data: UniversityUpdate, user: User = Depends(require_database_permission)):
    """Update university"""
    try:
        async with get_db_connection() as conn:
            query = """
            UPDATE universities SET
                university_code = $2, name = $3, country = $4, province_state = $5,
                city = $6, address = $7, website = $8, university_type = $9,
                languages = $10, year_established = $11, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING *
            """
            
            result = await conn.fetchrow(
                query,
                university_id,
                university_data.university_code,
                university_data.name,
                university_data.country,
                university_data.province_state,
                university_data.city,
                university_data.address,
                university_data.website,
                university_data.university_type,
                university_data.languages,
                university_data.year_established
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="University not found")
            
            return {"success": True, "university": dict(result)}
            
    except Exception as e:
        logger.error(f"Error updating university: {e}")
        raise HTTPException(status_code=500, detail="Failed to update university")

@app.delete("/api/v1/admin/universities/{university_id}")
async def admin_delete_university(request: Request, university_id: int, user: User = Depends(require_database_permission)):
    """Delete university"""
    try:
        async with get_db_connection() as conn:
            # Check if university has professors
            prof_count = await conn.fetchval(
                "SELECT COUNT(*) FROM professors WHERE university_code = (SELECT university_code FROM universities WHERE id = $1)",
                university_id
            )
            
            if prof_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot delete university: {prof_count} professors are associated with it"
                )
            
            result = await conn.fetchrow("DELETE FROM universities WHERE id = $1 RETURNING *", university_id)
            
            if not result:
                raise HTTPException(status_code=404, detail="University not found")
            
            return {"success": True, "message": "University deleted successfully"}
            
    except Exception as e:
        logger.error(f"Error deleting university: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete university")

@app.get("/api/v1/admin/professors")
async def admin_get_professors(
    request: Request,
    user: User = Depends(require_database_permission),
    university_code: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get professors for admin management"""
    try:
        async with get_db_connection() as conn:
            where_conditions = []
            params = []
            
            base_query = """
            SELECT 
                p.id, p.faculty_id, p.name, p.first_name, p.last_name, p.middle_names,
                p.degrees, p.research_areas, p.university_code, p.faculty, p.department,
                p.position, p.full_time, p.adjunct, p.uni_email, p.website,
                p.google_scholar, p.orcid, p.linkedin, p.created_at, p.updated_at,
                u.name as university_name
            FROM professors p
            LEFT JOIN universities u ON p.university_code = u.university_code
            """
            
            # Add filters
            if university_code:
                where_conditions.append(f"p.university_code = ${len(params)+1}")
                params.append(university_code)
            
            if department:
                where_conditions.append(f"p.department ILIKE ${len(params)+1}")
                params.append(f"%{department}%")
            
            if search:
                where_conditions.append(f"(p.name ILIKE ${len(params)+1} OR p.faculty_id ILIKE ${len(params)+1} OR p.research_areas ILIKE ${len(params)+1})")
                params.append(f"%{search}%")
                
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            base_query += f" ORDER BY p.name LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
            params.extend([limit, offset])
            
            professors = await conn.fetch(base_query, *params)
            
            # Count total
            count_query = "SELECT COUNT(*) FROM professors p"
            if where_conditions:
                count_query += " WHERE " + " AND ".join(where_conditions)
            
            total_count = await conn.fetchval(count_query, *params[:-2])
            
            return {
                "professors": [dict(p) for p in professors],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
            
    except Exception as e:
        logger.error(f"Error fetching professors: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch professors")

@app.post("/api/v1/admin/professors")
async def admin_create_professor(request: Request, professor_data: ProfessorCreate, user: User = Depends(require_database_permission)):
    """Create new professor"""
    try:
        async with get_db_connection() as conn:
            query = """
            INSERT INTO professors 
            (faculty_id, name, first_name, last_name, middle_names, degrees, research_areas,
             university_code, faculty, department, position, full_time, adjunct, uni_email,
             website, google_scholar, orcid, linkedin)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            RETURNING *
            """
            
            # Build full name if not provided
            full_name = professor_data.name
            if not full_name:
                name_parts = [professor_data.first_name, professor_data.middle_names, professor_data.last_name]
                full_name = ' '.join(part for part in name_parts if part)
            
            result = await conn.fetchrow(
                query,
                professor_data.faculty_id,
                full_name,
                professor_data.first_name,
                professor_data.last_name,
                professor_data.middle_names,
                professor_data.degrees,
                professor_data.research_areas,
                professor_data.university_code,
                professor_data.faculty,
                professor_data.department,
                professor_data.position,
                professor_data.full_time,
                professor_data.adjunct,
                professor_data.uni_email,
                professor_data.website,
                professor_data.google_scholar,
                professor_data.orcid,
                professor_data.linkedin
            )
            
            return {"success": True, "professor": dict(result)}
            
    except Exception as e:
        logger.error(f"Error creating professor: {e}")
        raise HTTPException(status_code=500, detail="Failed to create professor")

@app.put("/api/v1/admin/professors/{professor_id}")
async def admin_update_professor(request: Request, professor_id: int, professor_data: ProfessorUpdate, user: User = Depends(require_database_permission)):
    """Update professor"""
    try:
        async with get_db_connection() as conn:
            query = """
            UPDATE professors SET
                faculty_id = $2, name = $3, first_name = $4, last_name = $5, middle_names = $6,
                degrees = $7, research_areas = $8, university_code = $9, faculty = $10,
                department = $11, position = $12, full_time = $13, adjunct = $14,
                uni_email = $15, website = $16, google_scholar = $17, orcid = $18,
                linkedin = $19, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING *
            """
            
            # Build full name if individual name parts are provided but name is not
            full_name = professor_data.name
            if not full_name and (professor_data.first_name or professor_data.last_name):
                name_parts = [professor_data.first_name, professor_data.middle_names, professor_data.last_name]
                full_name = ' '.join(part for part in name_parts if part)
            
            result = await conn.fetchrow(
                query,
                professor_id,
                professor_data.faculty_id,
                full_name,
                professor_data.first_name,
                professor_data.last_name,
                professor_data.middle_names,
                professor_data.degrees,
                professor_data.research_areas,
                professor_data.university_code,
                professor_data.faculty,
                professor_data.department,
                professor_data.position,
                professor_data.full_time,
                professor_data.adjunct,
                professor_data.uni_email,
                professor_data.website,
                professor_data.google_scholar,
                professor_data.orcid,
                professor_data.linkedin
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Professor not found")
            
            return {"success": True, "professor": dict(result)}
            
    except Exception as e:
        logger.error(f"Error updating professor: {e}")
        raise HTTPException(status_code=500, detail="Failed to update professor")

@app.delete("/api/v1/admin/professors/{professor_id}")
async def admin_delete_professor(request: Request, professor_id: int, user: User = Depends(require_database_permission)):
    """Delete professor"""
    try:
        async with get_db_connection() as conn:
            result = await conn.fetchrow("DELETE FROM professors WHERE id = $1 RETURNING *", professor_id)
            
            if not result:
                raise HTTPException(status_code=404, detail="Professor not found")
            
            return {"success": True, "message": "Professor deleted successfully"}
            
    except Exception as e:
        logger.error(f"Error deleting professor: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete professor")

@app.get("/api/v1/admin/countries")
async def admin_get_countries(request: Request, user: User = Depends(require_database_permission)):
    """Get countries list derived from universities"""
    try:
        async with get_db_connection() as conn:
            countries = await conn.fetch("""
                SELECT 
                    country,
                    COUNT(*) as university_count,
                    COUNT(DISTINCT province_state) as province_count
                FROM universities 
                WHERE country IS NOT NULL AND country != ''
                GROUP BY country
                ORDER BY country
            """)
            
            return {"countries": [dict(c) for c in countries]}
            
    except Exception as e:
        logger.error(f"Error fetching countries: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch countries")

@app.get("/api/v1/admin/database/stats")
async def admin_database_stats(request: Request, user: User = Depends(require_database_permission)):
    """Get database statistics for admin dashboard"""
    try:
        async with get_db_connection() as conn:
            stats = {}
            
            # Basic counts
            stats['universities'] = await conn.fetchval("SELECT COUNT(*) FROM universities") or 0
            stats['professors'] = await conn.fetchval("SELECT COUNT(*) FROM professors") or 0
            stats['countries'] = await conn.fetchval("SELECT COUNT(DISTINCT country) FROM universities WHERE country IS NOT NULL") or 0
            
            # Universities by country
            country_stats = await conn.fetch("""
                SELECT country, COUNT(*) as count 
                FROM universities 
                WHERE country IS NOT NULL AND country != ''
                GROUP BY country 
                ORDER BY count DESC 
                LIMIT 10
            """)
            stats['universities_by_country'] = {row['country']: row['count'] for row in country_stats}
            
            # Professors by university
            university_stats = await conn.fetch("""
                SELECT u.name, COUNT(p.id) as professor_count
                FROM universities u
                LEFT JOIN professors p ON u.university_code = p.university_code
                GROUP BY u.id, u.name
                ORDER BY professor_count DESC
                LIMIT 10
            """)
            stats['professors_by_university'] = [
                {"university": row['name'], "count": row['professor_count']} 
                for row in university_stats
            ]
            
            # Recent additions
            recent_universities = await conn.fetchval("""
                SELECT COUNT(*) FROM universities 
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
            """) or 0
            
            recent_professors = await conn.fetchval("""
                SELECT COUNT(*) FROM professors 
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
            """) or 0
            
            stats['recent_additions'] = {
                'universities': recent_universities,
                'professors': recent_professors
            }
            
            return stats
            
    except Exception as e:
        logger.error(f"Error fetching database stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch database stats")

# Favicon route to prevent 404 errors
@app.get("/favicon.ico")
async def get_favicon(request: Request):
    """Return 204 No Content for favicon to prevent 404 errors"""
    return Response(status_code=204)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8008, log_level="info") 