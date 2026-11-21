import re
import difflib
from typing import List, Dict, Any, Optional
from app.models.schemas import ChangedFile

HUNK_HEADER_PATTERN = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)")

class DiffEngine:
    """
    Parses and processes git unified diffs, extracting precise line mappings,
    file changes, additions, deletions, and context.
    """

    @staticmethod
    def generate_manual_diff(original_code: str, updated_code: str, filename: str = "snippet.py") -> str:
        """
        Generates a standard unified diff from original and updated code strings.
        """
        orig_lines = original_code.splitlines(keepends=True)
        upd_lines = updated_code.splitlines(keepends=True)
        diff_lines = list(difflib.unified_diff(
            orig_lines,
            upd_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            n=3
        ))
        return "".join(diff_lines)

    @staticmethod
    def normalize_diff_input(
        original_code: Optional[str] = None,
        updated_code: Optional[str] = None,
        raw_diff: Optional[str] = None,
        filename: str = "snippet.py"
    ) -> str:
        """
        Normalizes input by either using raw diff directly or computing unified diff.
        """
        if raw_diff and raw_diff.strip():
            return raw_diff.strip()
        orig = original_code or ""
        upd = updated_code or ""
        return DiffEngine.generate_manual_diff(orig, upd, filename=filename)

    @staticmethod
    def parse_unified_diff(diff_text: str) -> List[ChangedFile]:
        """
        Parses a full multi-file unified diff into structured ChangedFile objects.
        Handles standard git diffs, unified diffs, and bare hunks.
        """
        if not diff_text or not diff_text.strip():
            return []

        files: List[ChangedFile] = []
        current_file: Optional[Dict[str, Any]] = None
        current_hunks: List[str] = []

        lines = diff_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]

            if line.startswith("diff --git"):
                if current_file:
                    current_file["diff_hunks"] = "\n".join(current_hunks)
                    files.append(ChangedFile(**current_file))
                    current_hunks = []

                # Extract file paths: diff --git a/path b/path
                parts = line.split(" ")
                old_path = parts[2][2:] if len(parts) > 2 and parts[2].startswith("a/") else ""
                new_path = parts[3][2:] if len(parts) > 3 and parts[3].startswith("b/") else old_path
                current_file = {
                    "file_path": new_path or old_path or "unknown",
                    "status": "modified",
                    "additions": 0,
                    "deletions": 0,
                    "old_path": old_path if old_path != new_path else None,
                    "diff_hunks": ""
                }
            elif line.startswith("new file mode"):
                if current_file:
                    current_file["status"] = "added"
            elif line.startswith("deleted file mode"):
                if current_file:
                    current_file["status"] = "deleted"
            elif line.startswith("similarity index"):
                if current_file:
                    current_file["status"] = "renamed"
            elif line.startswith("--- ") or line.startswith("+++ "):
                # diff headers
                path = line[4:].strip()
                if path.startswith("a/") or path.startswith("b/"):
                    path = path[2:]
                if not current_file:
                    current_file = {
                        "file_path": path or "snippet.py",
                        "status": "modified",
                        "additions": 0,
                        "deletions": 0,
                        "old_path": None,
                        "diff_hunks": ""
                    }
                elif current_file and current_file["file_path"] in ("unknown", ""):
                    current_file["file_path"] = path
            elif line.startswith("@@"):
                if not current_file:
                    current_file = {
                        "file_path": "snippet.py",
                        "status": "modified",
                        "additions": 0,
                        "deletions": 0,
                        "old_path": None,
                        "diff_hunks": ""
                    }
                current_hunks.append(line)
            else:
                if not current_file and (line.startswith("+") or line.startswith("-")):
                    current_file = {
                        "file_path": "snippet.py",
                        "status": "modified",
                        "additions": 0,
                        "deletions": 0,
                        "old_path": None,
                        "diff_hunks": ""
                    }
                if current_file:
                    if line.startswith("+") and not line.startswith("+++"):
                        current_file["additions"] += 1
                        current_hunks.append(line)
                    elif line.startswith("-") and not line.startswith("---"):
                        current_file["deletions"] += 1
                        current_hunks.append(line)
                    elif line.startswith(" ") or line.strip() == "":
                        current_hunks.append(line)
            i += 1

        if current_file:
            current_file["diff_hunks"] = "\n".join(current_hunks)
            files.append(ChangedFile(**current_file))

        return files

    @staticmethod
    def extract_line_ranges(hunks: str) -> List[Dict[str, Any]]:
        """
        Parses diff hunks to identify modified line numbers in the new file.
        Returns list of ranges: [{'start': int, 'end': int, 'header': str}]
        """
        ranges = []
        for line in hunks.splitlines():
            match = HUNK_HEADER_PATTERN.match(line)
            if match:
                new_start = int(match.group(3))
                new_len = int(match.group(4)) if match.group(4) else 1
                ranges.append({
                    "start": new_start,
                    "end": new_start + max(new_len - 1, 0),
                    "header": line
                })
        return ranges
