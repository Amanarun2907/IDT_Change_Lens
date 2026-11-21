import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from git import Repo, GitCommandError
from app.security.repository_sandbox import RepositorySandbox
from app.security.validators import validate_git_ref, safe_join_path

logger = logging.getLogger(__name__)

IGNORED_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__",
    "dist", "build", "target", ".idea", ".vscode", "coverage", ".pytest_cache"
}

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2",
    ".ttf", ".eot", ".mp4", ".zip", ".tar", ".gz", ".pyc", ".class", ".exe", ".bin"
}

class RepositoryManager:
    """
    Manages isolated repository retrieval, branch checking, and project structure detection.
    """
    def __init__(self, sandbox: RepositorySandbox, token: Optional[str] = None):
        self.sandbox = sandbox
        self.token = token
        self.repo_dir: Optional[Path] = None

    def clone_or_fetch(self, repo_url: str, base_ref: str = "main", target_ref: Optional[str] = None) -> Path:
        """
        Clones repository into the sandbox workspace.
        """
        workspace = self.sandbox.create()
        self.repo_dir = workspace / "repo"

        # Embed token in clone URL safely if provided
        clone_url = repo_url
        if self.token:
            if clone_url.startswith("https://"):
                clone_url = f"https://x-access-token:{self.token}@{clone_url[8:]}"

        validated_base = validate_git_ref(base_ref) if base_ref else "main"

        try:
            logger.info(f"Cloning {repo_url} into {self.repo_dir} (ref: {validated_base}, depth: 1)")
            # Ultra-fast shallow clone: depth 1 and single branch only
            repo = Repo.clone_from(
                clone_url,
                str(self.repo_dir),
                depth=1,
                single_branch=True,
                branch=validated_base,
                env={"GIT_TERMINAL_PROMPT": "0"}
            )
            self.sandbox.check_size()
            return self.repo_dir
        except GitCommandError as e:
            error_msg = str(e)
            if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                raise ValueError("Authentication required or token invalid to access this repository.")
            elif "not found" in error_msg:
                raise ValueError(f"Repository {repo_url} not found.")
            raise ValueError(f"Git clone failed: {error_msg}")

    def inspect_project_metadata(self) -> Dict[str, Any]:
        """
        Detects languages, frameworks, dependencies, and file structures.
        """
        if not self.repo_dir or not self.repo_dir.exists():
            return {
                "languages": [],
                "frameworks": [],
                "dependencies": [],
                "total_source_files": 0
            }

        language_counts: Dict[str, int] = {}
        frameworks = set()
        dependencies = set()
        source_files = []

        for root, dirs, files in os.walk(self.repo_dir):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                ext = Path(file).suffix.lower()
                if ext in IGNORED_EXTENSIONS:
                    continue

                full_path = Path(root) / file
                rel_path = str(full_path.relative_to(self.repo_dir)).replace("\\", "/")
                source_files.append(rel_path)

                # Language detection
                if ext in [".py"]:
                    language_counts["Python"] = language_counts.get("Python", 0) + 1
                elif ext in [".ts", ".tsx"]:
                    language_counts["TypeScript"] = language_counts.get("TypeScript", 0) + 1
                elif ext in [".js", ".jsx"]:
                    language_counts["JavaScript"] = language_counts.get("JavaScript", 0) + 1
                elif ext in [".java"]:
                    language_counts["Java"] = language_counts.get("Java", 0) + 1
                elif ext in [".go"]:
                    language_counts["Go"] = language_counts.get("Go", 0) + 1
                elif ext in [".c", ".cpp", ".h", ".hpp"]:
                    language_counts["C/C++"] = language_counts.get("C/C++", 0) + 1
                elif ext in [".rs"]:
                    language_counts["Rust"] = language_counts.get("Rust", 0) + 1

                # Framework and Dependency detection
                if file == "package.json":
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            pkg = json.load(f)
                            all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                            for dep in all_deps.keys():
                                dependencies.add(dep)
                                if dep in ["react", "next", "vue", "express", "fastify", "nest", "@angular/core"]:
                                    frameworks.add(dep)
                    except Exception:
                        pass
                elif file == "requirements.txt" or file == "Pipfile":
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip().split("==")[0].split(">=")[0].strip()
                                if line and not line.startswith("#"):
                                    dependencies.add(line)
                                    if line.lower() in ["fastapi", "django", "flask", "tornado", "celery", "langchain"]:
                                        frameworks.add(line)
                    except Exception:
                        pass

        sorted_langs = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
        detected_languages = [lang for lang, _ in sorted_langs]

        return {
            "languages": detected_languages or ["Python"],
            "frameworks": list(frameworks),
            "dependencies": list(dependencies)[:50],
            "total_source_files": len(source_files),
            "source_files": source_files
        }

    def read_file_content(self, relative_path: str, max_lines: int = 400) -> Optional[str]:
        """
        Safely reads a file with line limit and path traversal guard.
        """
        if not self.repo_dir or not self.repo_dir.exists():
            return None
        try:
            target = safe_join_path(self.repo_dir, relative_path)
            if not target.exists() or target.is_dir():
                return None
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = [f.readline() for _ in range(max_lines)]
                return "".join(lines)
        except Exception as e:
            logger.warning(f"Failed to read file {relative_path}: {e}")
            return None
