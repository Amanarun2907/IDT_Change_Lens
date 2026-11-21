import re
import socket
import ipaddress
from urllib.parse import urlparse
from pathlib import Path

# Disallowed IP ranges for SSRF defense
DISALLOWED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / Cloud metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

SAFE_GIT_REF_PATTERN = re.compile(r"^[a-zA-Z0-9_\-./#^@~]+$")
GITHUB_REPO_URL_PATTERN = re.compile(
    r"^https://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$"
)
GITHUB_PR_URL_PATTERN = re.compile(
    r"^https://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)/pull/(\d+)/?$"
)

def validate_github_url(url: str) -> dict:
    """
    Validates a GitHub repository or PR URL against SSRF and strict format.
    Returns parsed owner and repo name.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL cannot be empty")

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() != "https":
        raise ValueError("Only HTTPS GitHub URLs are allowed")

    if parsed.netloc.lower() not in ("github.com", "www.github.com"):
        raise ValueError("Only github.com URLs are supported")

    # SSRF DNS verification (ensure hostname does not resolve to private IP)
    try:
        resolved_ips = socket.getaddrinfo(parsed.hostname, None)
        for family, _, _, _, sockaddr in resolved_ips:
            ip = ipaddress.ip_address(sockaddr[0])
            for blocked in DISALLOWED_NETWORKS:
                if ip in blocked:
                    raise ValueError(f"SSRF violation: Host resolved to restricted IP {ip}")
    except socket.gaierror:
        # If running in an environment without external DNS (sandbox or offline test),
        # permit verified standard public hostnames
        if parsed.hostname in ("github.com", "www.github.com"):
            pass
        else:
            raise ValueError(f"Unable to resolve domain: {parsed.hostname}")

    # Check PR URL first
    pr_match = GITHUB_PR_URL_PATTERN.match(url.strip())
    if pr_match:
        owner, repo, pr_number = pr_match.groups()
        return {
            "type": "pr",
            "owner": owner,
            "repo": repo,
            "pr_number": int(pr_number),
            "normalized_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}"
        }

    # Check Repo URL
    repo_match = GITHUB_REPO_URL_PATTERN.match(url.strip())
    if repo_match:
        owner, repo = repo_match.groups()
        return {
            "type": "repo",
            "owner": owner,
            "repo": repo,
            "normalized_url": f"https://github.com/{owner}/{repo}"
        }

    raise ValueError("Invalid GitHub repository or Pull Request URL format")

def validate_git_ref(ref: str) -> str:
    """
    Validates git branch, tag, or commit reference to prevent command injection.
    """
    if not ref or not isinstance(ref, str):
        return "main"
    ref = ref.strip()
    if not SAFE_GIT_REF_PATTERN.match(ref):
        raise ValueError(f"Dangerous or invalid characters in git reference: {ref}")
    if ref.startswith("-") or "--" in ref or ".." in ref:
        raise ValueError(f"Unsafe git reference pattern: {ref}")
    return ref

def safe_join_path(base_dir: Path, relative_path: str) -> Path:
    """
    Ensures the target path is strictly within base_dir (Path Traversal defense).
    """
    base_resolved = base_dir.resolve()
    target_path = (base_dir / relative_path).resolve()
    try:
        target_path.relative_to(base_resolved)
    except ValueError:
        raise ValueError(f"Path traversal attempt detected: {relative_path}")
    return target_path
