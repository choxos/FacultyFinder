#!/usr/bin/env python3
"""
FacultyFinder - FastAPI Application
High-performance API for academic faculty discovery
"""

import os
import logging
import time
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Path, Request, status, Depends, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Database imports
import asyncpg
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# OAuth imports
from webapp.oauth import oauth, oauth_config, oauth_handler, init_oauth_handler, get_oauth_handler

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
    website: Optional[str] = None
    type: Optional[str] = None
    language: Optional[str] = None
    established: Optional[int] = None
    faculty_count: int = 0
    department_count: int = 0

class Professor(BaseModel):
    id: int
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    university_code: Optional[str] = None
    university_name: Optional[str] = None
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
    full_time: Optional[bool] = True

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

# Database helper functions
def get_db_connection():
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
async def homepage():
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
async def universities_page():
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
async def faculties_page():
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
async def countries_page():
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
async def ai_assistant_page():
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
async def get_stats():
    """Get summary statistics"""
    try:
        return await get_summary_statistics()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.get("/api/v1/universities", response_model=UniversitiesResponse)
async def get_universities(
    search: Optional[str] = Query(None, description="Search term for university name or location"),
    country: Optional[str] = Query(None, description="Filter by country"),
    province: Optional[str] = Query(None, description="Filter by province/state"),
    university_type: Optional[str] = Query(None, description="Filter by university type"),
    sort_by: str = Query("faculty_count", description="Sort by: faculty_count, name, location, year_established"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get universities with filtering and pagination"""
    try:
        async with get_db_connection() as conn:
            # Build WHERE clause
            where_conditions = ["u.name IS NOT NULL"]
            params = []
            param_count = 0
            
            if search:
                param_count += 2
                where_conditions.append(f"(u.name ILIKE ${param_count-1} OR u.city ILIKE ${param_count})")
                params.extend([f"%{search}%", f"%{search}%"])
            
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
            
            # Build ORDER BY clause
            order_mapping = {
                "faculty_count": "faculty_count DESC",
                "name": "u.name ASC",
                "location": "u.country ASC, u.city ASC",
                "established": "u.year_established DESC NULLS LAST"
            }
            order_clause = order_mapping.get(sort_by, "faculty_count DESC")
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Main query
            query = f"""
                SELECT u.id, u.name, u.country, u.city, u.university_code, 
                       COALESCE(u.province_state, '') as province_state,
                       COALESCE(u.address, '') as address,
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
                         u.address, u.website, u.university_type, u.languages, u.year_established
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
                    HAVING COUNT(p.id) >= 0
                    GROUP BY u.id
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
    search: Optional[str] = Query(None, description="Search term for professor name or research areas"),
    university: Optional[str] = Query(None, description="Filter by university code"),
    department: Optional[str] = Query(None, description="Filter by department"),
    research_area: Optional[str] = Query(None, description="Filter by research area"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type"),
    sort_by: str = Query("name", description="Sort by: name, university, department, publications, recent_publications"),
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
            order_mapping = {
                "name": "p.name ASC",
                "university": "u.name ASC",
                "department": "p.department ASC",
                "publications": "CAST(0 AS INTEGER) DESC NULLS LAST",
                "recent_publications": "CAST(0 AS INTEGER) DESC NULLS LAST"
            }
            order_clause = order_mapping.get(sort_by, "p.name ASC")
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Main query
            query = f"""
                SELECT p.id, p.faculty_id, p.name, COALESCE(p.uni_email, p.other_email, '') as email, p.university_code,
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
                       COALESCE(u.name, '') as university_name
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
            
            faculties = [Professor(**dict(row)) for row in rows]
            
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
async def get_countries():
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
async def get_professor(professor_id: str = Path(..., description="Professor ID (can be integer or university-code format)")):
    """Get individual professor details"""
    try:
        async with get_db_connection() as conn:
            # Handle both integer IDs and string format IDs like CA-ON-002-00001
            if professor_id.isdigit():
                # Legacy integer ID
                query = """
                    SELECT p.id, p.name, p.first_name, p.last_name, p.middle_names, p.other_name,
                           p.degrees, p.all_degrees_and_inst, p.all_degrees_only, p.research_areas,
                           p.university_code, p.faculty, p.department, p.other_departments,
                           p.primary_affiliation, p.memberships, p.canada_research_chair, p.director,
                           COALESCE(p.position, '') as position, 
                           COALESCE(p.full_time, true) as full_time, 
                           COALESCE(p.adjunct, false) as adjunct, 
                           p.uni_email as email, p.other_email,
                           p.uni_page, p.website, p.misc, p.twitter, p.linkedin, p.phone, p.fax,
                           p.google_scholar, p.scopus, p.web_of_science, p.orcid, p.researchgate,
                           p.academicedu, p.created_at, p.updated_at,
                           COALESCE(p.publication_count, 0) as publication_count,
                           COALESCE(p.citation_count, 0) as citation_count,
                           COALESCE(p.h_index, 0) as h_index,
                           COALESCE(u.name, '') as university_name, 
                           COALESCE(u.city, '') as city, 
                           COALESCE(u.province_state, '') as province_state, 
                           COALESCE(u.country, '') as country, 
                           COALESCE(u.address, '') as address, 
                           COALESCE(u.website, '') as university_website
                    FROM professors p
                    LEFT JOIN universities u ON p.university_code = u.university_code
                    WHERE p.id = $1
                """
                params = [int(professor_id)]
            else:
                # New string format ID - extract university code and sequence
                if '-' in professor_id and len(professor_id.split('-')) >= 4:
                    # Format: CA-ON-002-00001
                    parts = professor_id.split('-')
                    university_code = '-'.join(parts[:3])  # CA-ON-002
                    sequence = parts[3]  # 00001
                    
                    # First try to find by professor_id_new field if it exists
                    query_by_id = """
                        SELECT p.id, p.name, p.first_name, p.last_name, p.middle_names, p.other_name,
                               p.degrees, p.all_degrees_and_inst, p.all_degrees_only, p.research_areas,
                               p.university_code, p.faculty, p.department, p.other_departments,
                               p.primary_affiliation, p.memberships, p.canada_research_chair, p.director,
                               COALESCE(p.position, '') as position, 
                               COALESCE(p.full_time, true) as full_time, 
                               COALESCE(p.adjunct, false) as adjunct, 
                               p.uni_email as email, p.other_email,
                               p.uni_page, p.website, p.misc, p.twitter, p.linkedin, p.phone, p.fax,
                               p.google_scholar, p.scopus, p.web_of_science, p.orcid, p.researchgate,
                               p.academicedu, p.created_at, p.updated_at,
                               COALESCE(p.publication_count, 0) as publication_count,
                               COALESCE(p.citation_count, 0) as citation_count,
                               COALESCE(p.h_index, 0) as h_index,
                               COALESCE(u.name, '') as university_name, 
                               COALESCE(u.city, '') as city, 
                               COALESCE(u.province_state, '') as province_state, 
                               COALESCE(u.country, '') as country, 
                               COALESCE(u.address, '') as address, 
                               COALESCE(u.website, '') as university_website
                        FROM professors p
                        LEFT JOIN universities u ON p.university_code = u.university_code
                        WHERE p.professor_id_new = $1
                    """
                    
                    # Try to find by professor_id_new field first
                    row = await conn.fetchrow(query_by_id, professor_id)
                    
                    if not row:
                        # Fallback: use university code + sequence with better ordering
                        query = """
                            SELECT p.id, p.name, p.first_name, p.last_name, p.middle_names, p.other_name,
                                   p.degrees, p.all_degrees_and_inst, p.all_degrees_only, p.research_areas,
                                   p.university_code, p.faculty, p.department, p.other_departments,
                                   p.primary_affiliation, p.memberships, p.canada_research_chair, p.director,
                                   COALESCE(p.position, '') as position, 
                                   COALESCE(p.full_time, true) as full_time, 
                                   COALESCE(p.adjunct, false) as adjunct, 
                                   p.uni_email as email, p.other_email,
                                   p.uni_page, p.website, p.misc, p.twitter, p.linkedin, p.phone, p.fax,
                                   p.google_scholar, p.scopus, p.web_of_science, p.orcid, p.researchgate,
                                   p.academicedu, p.created_at, p.updated_at,
                                   COALESCE(p.publication_count, 0) as publication_count,
                                   COALESCE(p.citation_count, 0) as citation_count,
                                   COALESCE(p.h_index, 0) as h_index,
                                   COALESCE(u.name, '') as university_name, 
                                   COALESCE(u.city, '') as city, 
                                   COALESCE(u.province_state, '') as province_state, 
                                   COALESCE(u.country, '') as country, 
                                   COALESCE(u.address, '') as address, 
                                   COALESCE(u.website, '') as university_website
                            FROM professors p
                            LEFT JOIN universities u ON p.university_code = u.university_code
                            WHERE p.university_code = $1
                            ORDER BY p.name, p.id
                            LIMIT 1 OFFSET $2
                        """
                        try:
                            offset = int(sequence) - 1  # Convert 00001 to 0-based index
                            if offset < 0:
                                raise HTTPException(status_code=400, detail="Invalid sequence number")
                            row = await conn.fetchrow(query, university_code, offset)
                        except ValueError:
                            raise HTTPException(status_code=400, detail="Invalid professor ID format")
                else:
                    raise HTTPException(status_code=400, detail="Invalid professor ID format")

            if not row:
                # Try one more fallback - check if it's actually an integer disguised as string
                try:
                    int_id = int(professor_id)
                    query = """
                        SELECT p.id, p.name, p.first_name, p.last_name, p.middle_names, p.other_name,
                               p.degrees, p.all_degrees_and_inst, p.all_degrees_only, p.research_areas,
                               p.university_code, p.faculty, p.department, p.other_departments,
                               p.primary_affiliation, p.memberships, p.canada_research_chair, p.director,
                               COALESCE(p.position, '') as position, 
                               COALESCE(p.full_time, true) as full_time, 
                               COALESCE(p.adjunct, false) as adjunct, 
                               p.uni_email as email, p.other_email,
                               p.uni_page, p.website, p.misc, p.twitter, p.linkedin, p.phone, p.fax,
                               p.google_scholar, p.scopus, p.web_of_science, p.orcid, p.researchgate,
                               p.academicedu, p.created_at, p.updated_at,
                               COALESCE(p.publication_count, 0) as publication_count,
                               COALESCE(p.citation_count, 0) as citation_count,
                               COALESCE(p.h_index, 0) as h_index,
                               COALESCE(u.name, '') as university_name, 
                               COALESCE(u.city, '') as city, 
                               COALESCE(u.province_state, '') as province_state, 
                               COALESCE(u.country, '') as country, 
                               COALESCE(u.address, '') as address, 
                               COALESCE(u.website, '') as university_website
                        FROM professors p
                        LEFT JOIN universities u ON p.university_code = u.university_code
                        WHERE p.id = $1
                    """
                    row = await conn.fetchrow(query, int_id)
                except ValueError:
                    pass  # Not an integer, continue with 404
            
            if not row:
                raise HTTPException(status_code=404, detail="Professor not found")
            
            professor_data = dict(row)
            
            # Parse research areas if it's JSON
            if professor_data.get('research_areas'):
                try:
                    import json
                    if isinstance(professor_data['research_areas'], str):
                        professor_data['research_areas'] = json.loads(professor_data['research_areas'])
                except (json.JSONDecodeError, TypeError):
                    # If it's not JSON, treat as comma-separated string
                    if isinstance(professor_data['research_areas'], str):
                        professor_data['research_areas'] = professor_data['research_areas']
                    else:
                        professor_data['research_areas'] = ""
            
            # Ensure all required fields are present for the response
            professor_data['total_publications'] = professor_data.get('publication_count', 0)
            professor_data['primary_position'] = professor_data.get('position', '')
            
            return professor_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting professor {professor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Professor detail route
@app.get("/professor/{professor_id}")
async def get_professor_page(professor_id: str):
    """Serve professor detail page"""
    return FileResponse(os.path.join(static_dir, "professor.html"))

# University API endpoint
@app.get("/api/v1/university/{university_code}", response_model=University)
async def get_university_by_code(university_code: str):
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
async def get_university_page(university_code: str):
    """Serve university profile page"""
    return FileResponse(os.path.join(static_dir, "university.html"))

# Authentication routes
@app.get("/login")
async def get_login_page():
    """Serve login page"""
    return FileResponse(os.path.join(static_dir, "login.html"))

@app.get("/register")
async def get_register_page():
    """Serve registration page"""
    return FileResponse(os.path.join(static_dir, "register.html"))

# OAuth routes
@app.get("/auth/google")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    try:
        if not oauth_config.is_configured:
            raise HTTPException(status_code=500, detail="OAuth not configured")
        
        redirect_uri = request.url_for('oauth_callback')
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        logger.error(f"Google OAuth initiation error: {e}")
        return RedirectResponse(url="/login?error=oauth_failed")

@app.get("/auth/callback")
async def oauth_callback(request: Request):
    """Handle OAuth callback from Google"""
    try:
        oauth_handler = get_oauth_handler()
        auth_result = await oauth_handler.handle_callback(request)
        
        # Store user info in session
        request.session['user'] = auth_result['user']
        request.session['access_token'] = auth_result['access_token']
        
        # Redirect to dashboard or homepage
        return RedirectResponse(url="/?welcome=true")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(url="/login?error=auth_failed")

@app.get("/auth/logout")
async def logout(request: Request):
    """Logout user and clear session"""
    request.session.clear()
    return RedirectResponse(url="/?logout=true")

@app.get("/auth/user")
async def get_current_user(request: Request):
    """Get current authenticated user info"""
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@app.get("/health")
async def health_check():
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8008, log_level="info") 