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
from fastapi import FastAPI, HTTPException, Query, Path, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Database imports
import asyncpg
from pydantic import BaseModel, Field
from dotenv import load_dotenv

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
    year_established: Optional[int] = None
    faculty_count: int = 0

class Professor(BaseModel):
    id: int
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    university_code: Optional[str] = None
    university_name: Optional[str] = None
    department: Optional[str] = None
    primary_position: Optional[str] = None
    research_areas: Optional[str] = None
    total_publications: Optional[int] = 0
    publications_last_5_years: Optional[int] = 0

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
async def get_db_connection():
    """Get database connection from pool"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")
    return db_pool.acquire()

async def get_summary_statistics() -> StatsResponse:
    """Get homepage statistics"""
    async with await get_db_connection() as conn:
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
    async with await get_db_connection() as conn:
        query = """
            SELECT u.id, u.name, u.country, u.city, u.university_code, COALESCE(u.province_state, '') as province, u.year_established,
                   COUNT(p.id) as faculty_count
            FROM universities u
            LEFT JOIN professors p ON p.university_code = u.university_code
            WHERE u.name IS NOT NULL
            GROUP BY u.id, u.name, u.country, u.city, u.university_code, COALESCE(u.province_state, '') as province, u.year_established
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
        async with await get_db_connection() as conn:
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
            
            # Build ORDER BY clause
            order_mapping = {
                "faculty_count": "faculty_count DESC",
                "name": "u.name ASC",
                "location": "u.country ASC, u.city ASC",
                "year_established": "u.year_established DESC NULLS LAST"
            }
            order_clause = order_mapping.get(sort_by, "faculty_count DESC")
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Main query
            query = f"""
                SELECT u.id, u.name, u.country, u.city, u.university_code, COALESCE(u.province_state, '') as province, u.year_established,
                       COUNT(p.id) as faculty_count
                FROM universities u
                LEFT JOIN professors p ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
                GROUP BY u.id, u.name, u.country, u.city, u.university_code, COALESCE(u.province_state, '') as province, u.year_established
                HAVING COUNT(p.id) > 0
                ORDER BY {order_clause}
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            
            params.extend([per_page + 1, offset])  # +1 to check if there are more results
            
            rows = await conn.fetch(query, *params)
            
            # Check if there are more results
            has_more = len(rows) > per_page
            if has_more:
                rows = rows[:per_page]
            
            universities = [University(**dict(row)) for row in rows]
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(DISTINCT u.id)
                FROM universities u
                LEFT JOIN professors p ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
                GROUP BY u.id
                HAVING COUNT(p.id) > 0
            """
            
            # Remove LIMIT/OFFSET params for count
            count_params = params[:-2]
            count_rows = await conn.fetch(count_query, *count_params)
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
        async with await get_db_connection() as conn:
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
                where_conditions.append(f"p.primary_position ILIKE ${param_count}")
                params.append(f"%{employment_type}%")
            
            # Build ORDER BY clause
            order_mapping = {
                "name": "p.name ASC",
                "university": "u.name ASC",
                "department": "p.department ASC",
                "publications": "CAST(p.total_publications AS INTEGER) DESC NULLS LAST",
                "recent_publications": "CAST(p.publications_last_5_years AS INTEGER) DESC NULLS LAST"
            }
            order_clause = order_mapping.get(sort_by, "p.name ASC")
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Main query
            query = f"""
                SELECT p.id, p.name, p.email, p.university_code,
                       COALESCE(p.department, '') as department, p.primary_position, COALESCE(p.research_areas, '') as research_areas, p.total_publications,
                       p.publications_last_5_years, COALESCE(u.name, '') as university_name
                FROM professors p
                LEFT JOIN universities u ON p.university_code = u.university_code
                WHERE {' AND '.join(where_conditions)}
                ORDER BY {order_clause}
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            
            params.extend([per_page + 1, offset])  # +1 to check if there are more results
            
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
            
            # Remove pagination params for count
            count_params = params[:-2]
            total_count = await conn.fetchval(count_query, *count_params)
            
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
        async with await get_db_connection() as conn:
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

@app.get("/api/v1/professor/{professor_id}", response_model=Professor)
async def get_professor(professor_id: int = Path(..., description="Professor ID")):
    """Get individual professor details"""
    try:
        async with await get_db_connection() as conn:
            query = """
                SELECT p.*, COALESCE(u.name, '') as university_name
                FROM professors p
                LEFT JOIN universities u ON p.university_code = u.university_code
                WHERE p.id = $1
            """
            
            row = await conn.fetchrow(query, professor_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Professor not found")
            
            return Professor(**dict(row))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting professor: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve professor")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with await get_db_connection() as conn:
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