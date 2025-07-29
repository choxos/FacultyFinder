#!/usr/bin/env python3
"""
Update FastAPI Endpoints to Use Faculty ID
Updates professor detail endpoint and other references to use faculty_id
"""

import re

def update_fastapi_for_faculty_id():
    """Update FastAPI endpoints to use faculty_id"""
    
    with open('webapp/main.py', 'r') as f:
        content = f.read()
    
    print("🔧 Updating FastAPI endpoints for faculty_id...")
    
    # Update professor detail endpoint to accept faculty_id
    old_professor_endpoint = r'@app\.get\("/api/v1/professor/\{professor_id\}"\)\s*async def get_professor\(professor_id: str = Path\(\.\.\., description="Professor ID \(can be integer or university-code format\)"\)\):'
    
    new_professor_endpoint = r'@app.get("/api/v1/professor/{faculty_id}")\nasync def get_professor(faculty_id: str = Path(..., description="Faculty ID (e.g., CA-ON-002-F-0001)")):'
    
    content = re.sub(old_professor_endpoint, new_professor_endpoint, content)
    
    # Update professor detail query to use faculty_id
    old_professor_query = r'''# Handle both integer IDs and string format IDs like CA-ON-002-00001
            if professor_id\.isdigit\(\):
                # Legacy integer ID
                query = """
                    SELECT p\.id, p\.name, p\.first_name, p\.last_name, p\.middle_names, p\.other_name,
                           p\.degrees, p\.all_degrees_and_inst, p\.all_degrees_only, p\.research_areas,
                           p\.university_code, p\.faculty, p\.department, p\.other_departments,
                           p\.primary_affiliation, p\.memberships, p\.canada_research_chair, p\.director,
                           COALESCE\(p\.position, ''\) as position, 
                           COALESCE\(p\.full_time, true\) as full_time, 
                           COALESCE\(p\.adjunct, false\) as adjunct, 
                           p\.uni_email as email, p\.other_email,
                           p\.uni_page, p\.website, p\.misc, p\.twitter, p\.linkedin, p\.phone, p\.fax,
                           p\.google_scholar, p\.scopus, p\.web_of_science, p\.orcid, p\.researchgate, p\.academicedu,
                           u\.name as university_name, u\.city, u\.province_state, u\.country
                    FROM professors p
                    LEFT JOIN universities u ON p\.university_code = u\.university_code
                    WHERE p\.id = \$1
                """
                result = await conn\.fetchrow\(query, int\(professor_id\)\)
            else:
                # New format with university code
                query = """
                    SELECT p\.id, p\.name, p\.first_name, p\.last_name, p\.middle_names, p\.other_name,
                           p\.degrees, p\.all_degrees_and_inst, p\.all_degrees_only, p\.research_areas,
                           p\.university_code, p\.faculty, p\.department, p\.other_departments,
                           p\.primary_affiliation, p\.memberships, p\.canada_research_chair, p\.director,
                           COALESCE\(p\.position, ''\) as position, 
                           COALESCE\(p\.full_time, true\) as full_time, 
                           COALESCE\(p\.adjunct, false\) as adjunct, 
                           p\.uni_email as email, p\.other_email,
                           p\.uni_page, p\.website, p\.misc, p\.twitter, p\.linkedin, p\.phone, p\.fax,
                           p\.google_scholar, p\.scopus, p\.web_of_science, p\.orcid, p\.researchgate, p\.academicedu,
                           u\.name as university_name, u\.city, u\.province_state, u\.country
                    FROM professors p
                    LEFT JOIN universities u ON p\.university_code = u\.university_code
                    WHERE p\.id = \$1
                """
                # Extract numeric ID from format like CA-ON-002-00001
                numeric_id = professor_id\.split\('-'\)[-1]
                result = await conn\.fetchrow\(query, int\(numeric_id\)\)'''
    
    new_professor_query = r'''# Query professor by faculty_id
            query = """
                SELECT p.id, p.faculty_id, p.name, p.first_name, p.last_name, p.middle_names, p.other_name,
                       p.degrees, p.all_degrees_and_inst, p.all_degrees_only, p.research_areas,
                       p.university_code, p.faculty, p.department, p.other_departments,
                       p.primary_affiliation, p.memberships, p.canada_research_chair, p.director,
                       COALESCE(p.position, '') as position, 
                       COALESCE(p.full_time, true) as full_time, 
                       COALESCE(p.adjunct, false) as adjunct, 
                       p.uni_email as email, p.other_email,
                       p.uni_page, p.website, p.misc, p.twitter, p.linkedin, p.phone, p.fax,
                       p.google_scholar, p.scopus, p.web_of_science, p.orcid, p.researchgate, p.academicedu,
                       u.name as university_name, u.city, u.province_state, u.country
                FROM professors p
                LEFT JOIN universities u ON p.university_code = u.university_code
                WHERE p.faculty_id = $1
            """
            result = await conn.fetchrow(query, faculty_id)'''
    
    content = re.sub(old_professor_query, new_professor_query, content, flags=re.DOTALL)
    
    # Update the professor result processing to include faculty_id
    old_result_processing = r'''if result:
            return \{
                "id": result\["id"\],
                "name": result\["name"\],
                "first_name": result\["first_name"\],
                "last_name": result\["last_name"\],
                "middle_names": result\["middle_names"\],
                "other_name": result\["other_name"\],
                "degrees": result\["degrees"\],
                "all_degrees_and_inst": result\["all_degrees_and_inst"\],
                "all_degrees_only": result\["all_degrees_only"\],
                "research_areas": result\["research_areas"\],
                "university_code": result\["university_code"\],
                "faculty": result\["faculty"\],
                "department": result\["department"\],
                "other_departments": result\["other_departments"\],
                "primary_affiliation": result\["primary_affiliation"\],
                "memberships": result\["memberships"\],
                "canada_research_chair": result\["canada_research_chair"\],
                "director": result\["director"\],
                "position": result\["position"\],
                "full_time": result\["full_time"\],
                "adjunct": result\["adjunct"\],
                "email": result\["email"\],
                "other_email": result\["other_email"\],
                "uni_page": result\["uni_page"\],
                "website": result\["website"\],
                "misc": result\["misc"\],
                "twitter": result\["twitter"\],
                "linkedin": result\["linkedin"\],
                "phone": result\["phone"\],
                "fax": result\["fax"\],
                "google_scholar": result\["google_scholar"\],
                "scopus": result\["scopus"\],
                "web_of_science": result\["web_of_science"\],
                "orcid": result\["orcid"\],
                "researchgate": result\["researchgate"\],
                "academicedu": result\["academicedu"\],
                "university_name": result\["university_name"\],
                "city": result\["city"\],
                "province_state": result\["province_state"\],
                "country": result\["country"\],
                "publication_count": 0,
                "citation_count": 0,
                "h_index": 0
            \}
        else:
            raise HTTPException\(status_code=404, detail=f"Professor with ID \{professor_id\} not found"\)'''
    
    new_result_processing = r'''if result:
            return {
                "id": result["id"],
                "faculty_id": result["faculty_id"],
                "name": result["name"],
                "first_name": result["first_name"],
                "last_name": result["last_name"],
                "middle_names": result["middle_names"],
                "other_name": result["other_name"],
                "degrees": result["degrees"],
                "all_degrees_and_inst": result["all_degrees_and_inst"],
                "all_degrees_only": result["all_degrees_only"],
                "research_areas": result["research_areas"],
                "university_code": result["university_code"],
                "faculty": result["faculty"],
                "department": result["department"],
                "other_departments": result["other_departments"],
                "primary_affiliation": result["primary_affiliation"],
                "memberships": result["memberships"],
                "canada_research_chair": result["canada_research_chair"],
                "director": result["director"],
                "position": result["position"],
                "full_time": result["full_time"],
                "adjunct": result["adjunct"],
                "email": result["email"],
                "other_email": result["other_email"],
                "uni_page": result["uni_page"],
                "website": result["website"],
                "misc": result["misc"],
                "twitter": result["twitter"],
                "linkedin": result["linkedin"],
                "phone": result["phone"],
                "fax": result["fax"],
                "google_scholar": result["google_scholar"],
                "scopus": result["scopus"],
                "web_of_science": result["web_of_science"],
                "orcid": result["orcid"],
                "researchgate": result["researchgate"],
                "academicedu": result["academicedu"],
                "university_name": result["university_name"],
                "city": result["city"],
                "province_state": result["province_state"],
                "country": result["country"],
                "publication_count": 0,
                "citation_count": 0,
                "h_index": 0
            }
        else:
            raise HTTPException(status_code=404, detail=f"Professor with faculty ID {faculty_id} not found")'''
    
    content = re.sub(old_result_processing, new_result_processing, content, flags=re.DOTALL)
    
    # Update faculties API query to include faculty_id in the response
    old_faculties_query = r'''query = f"""
                SELECT p\.id, p\.name, p\.first_name, p\.last_name, p\.position, p\.department,
                       p\.research_areas, u\.name as university_name, u\.city, u\.province_state, u\.country,
                       COALESCE\(p\.uni_email, p\.other_email, ''\) as email,
                       COALESCE\(p\.website, p\.uni_page, ''\) as profile_url,
                       0 as publication_count, 0 as citation_count, 0 as h_index
                FROM professors p
                LEFT JOIN universities u ON p\.university_code = u\.university_code
                \{where_clause\}
                \{order_clause\}
                LIMIT \$\{param_count \+ 1\} OFFSET \$\{param_count \+ 2\}
            """'''
    
    new_faculties_query = r'''query = f"""
                SELECT p.id, p.faculty_id, p.name, p.first_name, p.last_name, p.position, p.department,
                       p.research_areas, u.name as university_name, u.city, u.province_state, u.country,
                       COALESCE(p.uni_email, p.other_email, '') as email,
                       COALESCE(p.website, p.uni_page, '') as profile_url,
                       0 as publication_count, 0 as citation_count, 0 as h_index
                FROM professors p
                LEFT JOIN universities u ON p.university_code = u.university_code
                {where_clause}
                {order_clause}
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """'''
    
    content = re.sub(old_faculties_query, new_faculties_query, content, flags=re.DOTALL)
    
    # Update faculty response mapping to include faculty_id
    old_faculty_mapping = r'''"id": row\["id"\],
                "name": row\["name"\],
                "first_name": row\["first_name"\],
                "last_name": row\["last_name"\],
                "position": row\["position"\],
                "department": row\["department"\],
                "research_areas": row\["research_areas"\],
                "university_name": row\["university_name"\],
                "city": row\["city"\],
                "province_state": row\["province_state"\],
                "country": row\["country"\],
                "email": row\["email"\],
                "profile_url": row\["profile_url"\],
                "publication_count": row\["publication_count"\],
                "citation_count": row\["citation_count"\],
                "h_index": row\["h_index"\]'''
    
    new_faculty_mapping = r'''"id": row["id"],
                "faculty_id": row["faculty_id"],
                "name": row["name"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "position": row["position"],
                "department": row["department"],
                "research_areas": row["research_areas"],
                "university_name": row["university_name"],
                "city": row["city"],
                "province_state": row["province_state"],
                "country": row["country"],
                "email": row["email"],
                "profile_url": row["profile_url"],
                "publication_count": row["publication_count"],
                "citation_count": row["citation_count"],
                "h_index": row["h_index"]'''
    
    content = re.sub(old_faculty_mapping, new_faculty_mapping, content)
    
    # Update static route for professor pages to use faculty_id
    old_professor_route = r'@app\.get\("/professor/\{professor_id\}"\)\s*async def professor_detail\(professor_id: str\):'
    
    new_professor_route = r'@app.get("/professor/{faculty_id}")\nasync def professor_detail(faculty_id: str):'
    
    content = re.sub(old_professor_route, new_professor_route, content)
    
    # Write the updated content back
    with open('webapp/main.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated FastAPI endpoints for faculty_id")
    return True

def update_pydantic_models():
    """Update Pydantic models to include faculty_id"""
    
    with open('webapp/main.py', 'r') as f:
        content = f.read()
    
    print("🔧 Updating Pydantic models for faculty_id...")
    
    # Find and update Professor model
    professor_model_pattern = r'class Professor\(BaseModel\):(.*?)(?=class|\Z)'
    
    if re.search(professor_model_pattern, content, re.DOTALL):
        # Add faculty_id field to Professor model
        old_professor_model = r'class Professor\(BaseModel\):\s*id: int\s*name: str'
        new_professor_model = r'class Professor(BaseModel):\n    id: int\n    faculty_id: str\n    name: str'
        
        content = re.sub(old_professor_model, new_professor_model, content)
    
    # Update Faculty model if it exists
    faculty_model_pattern = r'class Faculty\(BaseModel\):(.*?)(?=class|\Z)'
    
    if re.search(faculty_model_pattern, content, re.DOTALL):
        old_faculty_model = r'class Faculty\(BaseModel\):\s*id: int\s*name: str'
        new_faculty_model = r'class Faculty(BaseModel):\n    id: int\n    faculty_id: str\n    name: str'
        
        content = re.sub(old_faculty_model, new_faculty_model, content)
    
    with open('webapp/main.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated Pydantic models for faculty_id")
    return True

def main():
    """Main function"""
    print("🔧 Updating FastAPI for Faculty ID System")
    print("========================================")
    
    if update_fastapi_for_faculty_id():
        print("✅ FastAPI endpoints updated")
    else:
        print("❌ Failed to update FastAPI endpoints")
        return False
    
    if update_pydantic_models():
        print("✅ Pydantic models updated")
    else:
        print("❌ Failed to update Pydantic models")
        return False
    
    print("🎉 FastAPI successfully updated for faculty_id system!")
    return True

if __name__ == "__main__":
    main() 