import pytest
from app.security.validators import validate_github_url, validate_git_ref

def test_valid_github_repo_url():
    res = validate_github_url("https://github.com/torvalds/linux")
    assert res["type"] == "repo"
    assert res["owner"] == "torvalds"
    assert res["repo"] == "linux"

def test_valid_github_pr_url():
    res = validate_github_url("https://github.com/facebook/react/pull/12345")
    assert res["type"] == "pr"
    assert res["owner"] == "facebook"
    assert res["repo"] == "react"
    assert res["pr_number"] == 12345

def test_invalid_urls():
    with pytest.raises(ValueError):
        validate_github_url("http://github.com/insecure/repo") # HTTP blocked
    with pytest.raises(ValueError):
        validate_github_url("https://evil.com/fake/repo")
    with pytest.raises(ValueError):
        validate_github_url("https://127.0.0.1/fake/repo")

def test_git_ref_validation():
    assert validate_git_ref("main") == "main"
    assert validate_git_ref("feat/new-auth-v2") == "feat/new-auth-v2"
    with pytest.raises(ValueError):
        validate_git_ref("main; rm -rf /")
    with pytest.raises(ValueError):
        validate_git_ref("--dangerous-flag")
