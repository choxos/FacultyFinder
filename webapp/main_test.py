#!/usr/bin/env python3
"""
FacultyFinder - FastAPI Application (Test Version)
Simplified version for local testing without database dependency
"""

import os
import logging
from typing import List, Dict, Optional, Any

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query, Path, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Pydantic models
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FacultyFinder API",
    description="High-performance API for discovering academic faculty and research collaborators worldwide",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
import os
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
    professor_id: Optional[str] = None  # External string identifier (e.g., "CA-ON-002-00001")
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

# Mock data for testing
MOCK_STATS = StatsResponse(
    total_professors=272,
    total_universities=101,
    total_publications=12450,
    countries_count=15
)

MOCK_UNIVERSITIES = [
    University(id=1, name="McMaster University", country="Canada", city="Hamilton", 
               university_code="MCMASTER", province="Ontario", year_established=1887, faculty_count=85),
    University(id=2, name="University of Toronto", country="Canada", city="Toronto", 
               university_code="UTORONTO", province="Ontario", year_established=1827, faculty_count=156),
    University(id=3, name="Harvard University", country="United States", city="Cambridge", 
               university_code="HARVARD", province="Massachusetts", year_established=1636, faculty_count=203),
    University(id=4, name="Stanford University", country="United States", city="Stanford", 
               university_code="STANFORD", province="California", year_established=1885, faculty_count=178),
    University(id=5, name="MIT", country="United States", city="Cambridge", 
               university_code="MIT", province="Massachusetts", year_established=1861, faculty_count=145),
]

MOCK_PROFESSORS = [
    Professor(id=1, professor_id="CA-ON-002-00001", name="Dr. John Smith", email="john.smith@mcmaster.ca", 
              university_code="MCMASTER", university_name="McMaster University",
              department="Health Sciences", primary_position="Professor",
              research_areas="Epidemiology|Public Health|Biostatistics", 
              total_publications=89, publications_last_5_years=23),
    Professor(id=2, professor_id="CA-ON-001-00001", name="Dr. Sarah Johnson", email="s.johnson@utoronto.ca",
              university_code="UTORONTO", university_name="University of Toronto",
              department="Computer Science", primary_position="Associate Professor",
              research_areas="Machine Learning|AI|Data Science",
              total_publications=67, publications_last_5_years=34),
    Professor(id=3, professor_id="US-MA-001-00001", name="Dr. Michael Chen", email="mchen@harvard.edu",
              university_code="HARVARD", university_name="Harvard University", 
              department="Medicine", primary_position="Professor",
              research_areas="Cardiology|Clinical Research|Genetics",
              total_publications=156, publications_last_5_years=45),
]

MOCK_COUNTRIES = [
    Country(country="Canada", university_count=25, faculty_count=89),
    Country(country="United States", university_count=67, faculty_count=156),
    Country(country="United Kingdom", university_count=23, faculty_count=78),
]

# Routes

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Serve the homepage"""
    try:
        with open("static/index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FacultyFinder - Test Mode</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1 class="text-center">🎓 FacultyFinder (Test Mode)</h1>
                <p class="text-center lead">Testing FastAPI Migration</p>
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
        with open("static/universities.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Universities Page (Test Mode)</h1>")

@app.get("/faculties", response_class=HTMLResponse)
async def faculties_page():
    """Serve the faculties page"""
    try:
        with open("static/faculties.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Faculties Page (Test Mode)</h1>")

@app.get("/countries", response_class=HTMLResponse)
async def countries_page():
    """Serve the countries page"""
    try:
        with open("static/countries.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Countries Page (Test Mode)</h1>")

@app.get("/ai-assistant", response_class=HTMLResponse)
async def ai_assistant_page():
    """Serve the AI assistant page"""
    try:
        with open("static/ai-assistant.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>AI Assistant Page (Test Mode)</h1>")

# API Routes with mock data

@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats():
    """Get summary statistics"""
    return MOCK_STATS

@app.get("/api/v1/universities")
async def get_universities(
    search: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    sort_by: str = Query("faculty_count"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get universities with filtering and pagination"""
    universities = MOCK_UNIVERSITIES.copy()
    
    # Apply filters
    if search:
        universities = [u for u in universities if search.lower() in u.name.lower() or search.lower() in u.city.lower()]
    if country:
        universities = [u for u in universities if u.country == country]
    
    # Apply sorting
    if sort_by == "name":
        universities.sort(key=lambda x: x.name)
    elif sort_by == "faculty_count":
        universities.sort(key=lambda x: x.faculty_count, reverse=True)
    
    total_count = len(universities)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    return {
        "universities": universities[start_idx:end_idx],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "has_more": end_idx < total_count,
            "total_pages": (total_count + per_page - 1) // per_page
        }
    }

@app.get("/api/v1/faculties")
async def get_faculties(
    search: Optional[str] = Query(None),
    university: Optional[str] = Query(None),
    sort_by: str = Query("name"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get faculty with filtering and pagination"""
    faculties = MOCK_PROFESSORS.copy()
    
    # Apply filters
    if search:
        faculties = [f for f in faculties if search.lower() in f.name.lower() or 
                    (f.research_areas and search.lower() in f.research_areas.lower())]
    if university:
        faculties = [f for f in faculties if f.university_code == university]
    
    # Apply sorting
    if sort_by == "name":
        faculties.sort(key=lambda x: x.name)
    elif sort_by == "publications":
        faculties.sort(key=lambda x: x.total_publications or 0, reverse=True)
    
    total_count = len(faculties)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    return {
        "faculties": faculties[start_idx:end_idx],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "has_more": end_idx < total_count,
            "total_pages": (total_count + per_page - 1) // per_page
        }
    }

@app.get("/api/v1/countries", response_model=List[Country])
async def get_countries():
    """Get countries with university and faculty counts"""
    return MOCK_COUNTRIES

@app.get("/api/v1/professor/{professor_id}", response_model=Professor)
async def get_professor(professor_id: str = Path(...)):
    """Get individual professor details"""
    professor = next((p for p in MOCK_PROFESSORS if p.professor_id == professor_id), None)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    return professor

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "framework": "FastAPI",
        "mode": "test",
        "version": "2.0.0"
    }

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