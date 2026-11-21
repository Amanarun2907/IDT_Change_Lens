import re
from typing import Any, Union, Dict, List

SECRET_PATTERNS = [
    # GitHub Tokens
    (re.compile(r"(ghp_[a-zA-Z0-9]{36,40})"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"(github_pat_[a-zA-Z0-9_]{50,90})"), "[REDACTED_GITHUB_PAT]"),
    # Groq API Keys
    (re.compile(r"(gsk_[a-zA-Z0-9]{40,64})"), "[REDACTED_GROQ_KEY]"),
    # OpenAI API Keys
    (re.compile(r"(sk-[a-zA-Z0-9]{48,})"), "[REDACTED_OPENAI_KEY]"),
    (re.compile(r"(sk-proj-[a-zA-Z0-9_\-]{48,})"), "[REDACTED_OPENAI_KEY]"),
    # AWS Keys
    (re.compile(r"(AKIA[0-9A-Z]{16})"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"([0-9a-zA-Z/+]{40})(?=\s*#?\s*aws_secret)"), "[REDACTED_AWS_SECRET]"),
    # Slack / Discord Tokens
    (re.compile(r"(xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24})"), "[REDACTED_SLACK_TOKEN]"),
    # Private Keys
    (re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+ PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    # Generic password assignments in code
    (re.compile(r"""(?i)(password|secret|passwd|token|api_key|auth_token)\s*[:=]\s*["']([^"']{6,})["']"""), r'\1: "[REDACTED]"')
]

def redact_secrets(text: str) -> str:
    """
    Scans a string and replaces detected credentials and API keys with redacted tokens.
    """
    if not isinstance(text, str):
        return text

    redacted = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted

def deep_redact(data: Any) -> Any:
    """
    Recursively redacts secrets in dicts, lists, and strings.
    """
    if isinstance(data, str):
        return redact_secrets(data)
    elif isinstance(data, dict):
        return {k: deep_redact(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [deep_redact(item) for item in data]
    return data
