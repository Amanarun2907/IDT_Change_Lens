import httpx
import base64
from typing import Optional, Dict, Any, List
from app.config import settings

class GitHubClient:
    """
    High-performance client for interacting with GitHub REST API.
    Supports public repos and authenticated private repos with low latency.
    """
    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN or None
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ChangeLens-Agentic-Platform/1.0"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.headers = headers

    async def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetches repository metadata."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers=self.headers)
            if res.status_code == 404:
                raise ValueError(f"Repository '{owner}/{repo}' not found. If this is a private repository, please provide a valid GitHub Personal Access Token.")
            elif res.status_code == 401:
                raise ValueError("GitHub authentication failed. Please verify your token.")
            elif res.status_code == 403:
                raise ValueError("GitHub API rate limit exceeded or access forbidden. Provide a GitHub token in settings.")
            res.raise_for_status()
            return res.json()

    async def get_languages(self, owner: str, repo: str) -> List[str]:
        """Fetches language breakdown directly from GitHub in milliseconds."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/languages"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, headers=self.headers)
                if res.status_code == 200:
                    return list(res.json().keys())
        except Exception:
            pass
        return ["Python"]

    async def get_branches(self, owner: str, repo: str) -> List[str]:
        """Fetches list of branches."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/branches?per_page=100"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers=self.headers)
            if res.status_code != 200:
                return ["main", "master"]
            return [b["name"] for b in res.json()]

    async def get_commits(self, owner: str, repo: str, branch: str = "main", limit: int = 5) -> List[Dict[str, Any]]:
        """Fetches recent commits for a branch."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits?sha={branch}&per_page={limit}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return []

    async def get_commit_diff(self, owner: str, repo: str, sha: str) -> str:
        """Fetches unified diff of a specific commit directly from GitHub."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits/{sha}"
        diff_headers = dict(self.headers)
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(url, headers=diff_headers)
            if res.status_code == 200:
                return res.text
            return ""

    async def get_compare_diff(self, owner: str, repo: str, base: str, head: str) -> str:
        """Fetches raw unified diff between two branches or commits directly via GitHub API."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/compare/{base}...{head}"
        diff_headers = dict(self.headers)
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.get(url, headers=diff_headers)
            if res.status_code == 200:
                return res.text
            return ""

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Fetches Pull Request metadata."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers=self.headers)
            if res.status_code == 404:
                raise ValueError(f"Pull Request #{pr_number} in '{owner}/{repo}' not found.")
            elif res.status_code == 403:
                raise ValueError("GitHub API rate limit exceeded or access forbidden.")
            res.raise_for_status()
            return res.json()

    async def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetches list of changed files in a PR."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files?per_page=100"
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(url, headers=self.headers)
            res.raise_for_status()
            return res.json()

    async def get_pull_request_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetches raw unified diff of a PR."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        diff_headers = dict(self.headers)
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.get(url, headers=diff_headers)
            res.raise_for_status()
            return res.text

    async def compare_branches(self, owner: str, repo: str, base: str, head: str) -> Dict[str, Any]:
        """Compares two branches or commits."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/compare/{base}...{head}"
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.get(url, headers=self.headers)
            res.raise_for_status()
            return res.json()

    async def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> Optional[str]:
        """Fetches content of a specific file."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}?ref={ref}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url, headers=self.headers)
            if res.status_code == 200:
                data = res.json()
                if data.get("encoding") == "base64" and data.get("content"):
                    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            return None
