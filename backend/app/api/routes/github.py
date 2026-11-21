from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from app.security.validators import validate_github_url
from app.github.client import GitHubClient

router = APIRouter(prefix="/github", tags=["GitHub"])

class ValidateUrlRequest(BaseModel):
    url: str
    token: Optional[str] = None

@router.post("/validate")
async def validate_url(req: ValidateUrlRequest):
    try:
        info = validate_github_url(req.url)
        client = GitHubClient(token=req.token)
        repo_data = await client.get_repo_info(info["owner"], info["repo"])
        return {
            "valid": True,
            "info": info,
            "repo_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "default_branch": repo_data.get("default_branch", "main"),
            "private": repo_data.get("private", False)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub validation error: {str(e)}")

@router.get("/branches")
async def get_branches(repo_url: str = Query(...), token: Optional[str] = Query(None)):
    try:
        info = validate_github_url(repo_url)
        client = GitHubClient(token=token)
        branches = await client.get_branches(info["owner"], info["repo"])
        return {"branches": branches}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch branches: {str(e)}")
