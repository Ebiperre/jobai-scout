from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="JobAI Scout Backend")

# Enable CORS for frontend (e.g., React on localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for job data
class Job(BaseModel):
    id: str
    title: str
    company: str
    location: Optional[str]
    salary: Optional[str]
    url: str
    description: Optional[str]

# Endpoint to fetch jobs from RemoteOK
@app.get("/jobs", response_model=List[Job])
async def get_jobs(search: Optional[str] = None):
    try:
        url = "https://remoteok.com/api"
        if search:
            url += f"?tags={search}"
        response = requests.get(url, headers={"User-Agent": "JobAI Scout"})
        response.raise_for_status()
        data = response.json()
        
        # Skip the first item (RemoteOK metadata)
        jobs = data[1:] if isinstance(data, list) else []
        
        # Map to our Job model
        formatted_jobs = [
            Job(
                id=job.get("id", ""),
                title=job.get("position", "Unknown"),
                company=job.get("company", "Unknown"),
                location=job.get("location", None),
                salary=job.get("salary", None),
                url=job.get("url", ""),
                description=job.get("description", None)
            )
            for job in jobs
            if job.get("id")  # Ensure job has an ID
        ]
        return formatted_jobs
    except Exception as e:
        return {"error": str(e)}

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "JobAI Scout Backend is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)