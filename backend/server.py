from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from pydantic import BaseModel
from typing import List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="JobAI Scout Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY is missing in .env file!")

try:
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception as e:
    raise ValueError(f"Failed to initialize Supabase client: {str(e)}")

# Pydantic model for job data
class Job(BaseModel):
    id: str
    title: str
    company: str
    location: Optional[str]
    salary: Optional[str]
    url: str
    description: Optional[str]

# Endpoint to fetch jobs from RemoteOK and store in Supabase
@app.get("/jobs", response_model=List[Job])
async def get_jobs(search: Optional[str] = None):
    try:
        # Fetch from RemoteOK
        url = "https://remoteok.com/api"
        if search:
            url += f"?tags={search}"
        response = requests.get(url, headers={"User-Agent": "JobAI Scout"})
        response.raise_for_status()
        data = response.json()
        
        # Skip metadata
        jobs = data[1:] if isinstance(data, list) else []
        
        formatted_jobs = []
        for job in jobs:
            if not job.get("id"):
                continue
            
            # Check if job exists in DB by URL
            existing = supabase.table("jobs").select("*").eq("url", job.get("url", "")).execute()
            if existing.data:
                existing_job = existing.data[0]
                formatted_jobs.append(Job(
                    id=existing_job["id"],
                    title=existing_job["title"],
                    company=existing_job["company"],
                    location=existing_job["location"],
                    salary=existing_job["salary"],
                    url=existing_job["url"],
                    description=existing_job["description"]
                ))
            else:
                # Insert new job
                insert_data = {
                    "title": job.get("position", "Unknown"),
                    "company": job.get("company", "Unknown"),
                    "location": job.get("location", None),
                    "salary": job.get("salary", None),
                    "url": job.get("url", ""),
                    "description": job.get("description", None)
                }
                inserted = supabase.table("jobs").insert(insert_data).execute()
                if inserted.data:
                    new_job = inserted.data[0]
                    formatted_jobs.append(Job(
                        id=new_job["id"],
                        title=new_job["title"],
                        company=new_job["company"],
                        location=new_job["location"],
                        salary=new_job["salary"],
                        url=new_job["url"],
                        description=new_job["description"]
                    ))
        
        return formatted_jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

# Health check
@app.get("/")
async def root():
    return {"message": "JobAI Scout Backend is running with Supabase!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)