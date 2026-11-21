import re
from typing import List
from app.models.schemas import SecurityFinding, Severity, ChangedFile
from app.security.secret_redaction import redact_secrets

RULE_PATTERNS = [
    {
        "title": "Hardcoded Secret or API Key",
        "pattern": re.compile(r"""(?i)(api_key|secret|token|password|passwd|auth_token)\s*[:=]\s*["']([a-zA-Z0-9_\-\.]{12,})["']"""),
        "severity": Severity.CRITICAL,
        "cwe": "CWE-798",
        "explanation": "Credentials hardcoded in source code risk exposure across version control, build logs, and unauthorized clones.",
        "attack_scenario": "An attacker with read access to repository history extracts the credential to authenticate as an authorized service.",
        "potential_impact": "Unauthorized system access, data leakage, and service compromise.",
        "remediation": "Move credential to environment variables (e.g. os.getenv) or a secure secrets vault."
    },
    {
        "title": "Potential SQL Injection via String Formatting",
        "pattern": re.compile(r"""(?i)(?:execute|cursor\.execute|raw_sql|query)\s*\(\s*(?:f["'].*?\{|["'].*?%s|["'].*?\+).*?\)"""),
        "severity": Severity.HIGH,
        "cwe": "CWE-89",
        "explanation": "Dynamic SQL query constructed with unescaped string interpolation or concatenation allows arbitrary SQL commands.",
        "attack_scenario": "Attacker supplies malicious SQL fragments in user input to bypass authentication or extract sensitive tables.",
        "potential_impact": "Full database read/write compromise and data destruction.",
        "remediation": "Use parameterized queries or ORM query abstractions."
    },
    {
        "title": "Command Injection via Shell Execution",
        "pattern": re.compile(r"""(?i)(?:subprocess\.(?:call|Popen|run)\s*\(.*?shell\s*=\s*True|os\.system\s*\()"""),
        "severity": Severity.HIGH,
        "cwe": "CWE-78",
        "explanation": "Executing shell commands with shell=True or os.system with untrusted arguments enables arbitrary system command execution.",
        "attack_scenario": "Attacker injects shell metacharacters (; & | `) into arguments to execute arbitrary OS commands with server privileges.",
        "potential_impact": "Remote code execution, host system takeover.",
        "remediation": "Use subprocess.run with argument list (shell=False) and validate input."
    },
    {
        "title": "Insecure Deserialization via Pickle or Unsafe YAML",
        "pattern": re.compile(r"""(?i)(?:pickle\.loads?|yaml\.load\s*\(.*?Loader\s*=\s*yaml\.Loader)"""),
        "severity": Severity.HIGH,
        "cwe": "CWE-502",
        "explanation": "Deserializing untrusted streams using pickle or default YAML loaders allows arbitrary code execution via object reduction hooks.",
        "attack_scenario": "Attacker provides crafted serialized payload triggering __reduce__ arbitrary execution upon unpickling.",
        "potential_impact": "Arbitrary remote code execution in application process.",
        "remediation": "Use safe serialization formats (JSON) or yaml.safe_load."
    },
    {
        "title": "Unrestricted Path Traversal Risk",
        "pattern": re.compile(r"""(?i)(?:open|send_file)\s*\(\s*(?:os\.path\.join\s*\(.*?,?\s*(?:request|params|user|input|filename))"""),
        "severity": Severity.HIGH,
        "cwe": "CWE-22",
        "explanation": "File operations using untrusted filenames without path canonicalization validation allow escaping target directories.",
        "attack_scenario": "Attacker passes '../../../../etc/passwd' to access arbitrary filesystem resources.",
        "potential_impact": "Unauthorized file disclosure or overwriting critical system files.",
        "remediation": "Resolve absolute path and verify target is within allowed base directory."
    }
]

class StaticSecurityScanner:
    """
    Lightweight, fast rule-based security scanner to complement LLM agents.
    Scans modified hunks and source files.
    """

    @staticmethod
    def scan_changed_files(changed_files: List[ChangedFile]) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []

        for cf in changed_files:
            hunks = cf.diff_hunks or ""
            current_line = 1

            for line in hunks.splitlines():
                if line.startswith("@@"):
                    # Extract starting line
                    parts = line.split(" ")
                    if len(parts) > 2 and parts[2].startswith("+"):
                        try:
                            current_line = int(parts[2][1:].split(",")[0])
                        except Exception:
                            pass
                    continue

                if line.startswith("+") and not line.startswith("+++"):
                    # Scan added or modified line
                    for rule in RULE_PATTERNS:
                        match = rule["pattern"].search(line[1:])
                        if match:
                            raw_snippet = line[1:].strip()
                            safe_snippet = redact_secrets(raw_snippet)
                            findings.append(SecurityFinding(
                                vulnerability_title=rule["title"],
                                file_path=cf.file_path,
                                exact_line=current_line,
                                code_evidence=safe_snippet,
                                cwe=rule.get("cwe"),
                                explanation=rule["explanation"],
                                attack_scenario=rule["attack_scenario"],
                                potential_impact=rule["potential_impact"],
                                severity=rule["severity"],
                                confidence=0.95,
                                remediation=rule["remediation"]
                            ))
                    current_line += 1
                elif line.startswith(" "):
                    current_line += 1

        return findings
