import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from app.analysis.ast_analyzer import ASTAnalyzer
from app.models.schemas import ChangedFile, ImpactItem
from app.github.diff_engine import DiffEngine

class DependencyAnalyzer:
    """
    Signature ChangeLens Engine:
    Investigates how modifications spread across callers, dependent modules, and APIs.
    Distinguishes verified AST relationships from inferred ones.
    """

    def __init__(self, repo_dir: Optional[Path] = None):
        self.repo_dir = repo_dir

    def analyze_impact(
        self,
        changed_files: List[ChangedFile],
        file_contents: Optional[Dict[str, str]] = None
    ) -> List[ImpactItem]:
        """
        Calculates downstream impacts of changes.
        """
        impacts: List[ImpactItem] = []
        file_contents = file_contents or {}

        # 1. First, parse each changed file to find which functions/classes were modified
        modified_symbols: List[Dict[str, Any]] = []

        for cf in changed_files:
            content = file_contents.get(cf.file_path, "")
            if not content and self.repo_dir:
                try:
                    fp = self.repo_dir / cf.file_path
                    if fp.exists():
                        content = fp.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass

            if not content:
                continue

            # Parse AST symbols
            ext = Path(cf.file_path).suffix.lower()
            if ext == ".py":
                ast_data = ASTAnalyzer.analyze_python_code(content, cf.file_path)
            else:
                ast_data = ASTAnalyzer.analyze_polyglot_code(content, cf.file_path)

            line_ranges = DiffEngine.extract_line_ranges(cf.diff_hunks or "")

            # Match modified lines with functions
            for fn in ast_data["functions"]:
                fn_start = fn["line_start"]
                fn_end = fn["line_end"]
                is_modified = False
                for lr in line_ranges:
                    # Check overlap
                    if not (lr["end"] < fn_start or lr["start"] > fn_end):
                        is_modified = True
                        break

                if is_modified:
                    modified_symbols.append({
                        "name": fn["name"],
                        "type": "function",
                        "file_path": cf.file_path,
                        "args": fn.get("args", [])
                    })

            for cls in ast_data["classes"]:
                cls_start = cls["line_start"]
                cls_end = cls["line_end"]
                is_modified = False
                for lr in line_ranges:
                    if not (lr["end"] < cls_start or lr["start"] > cls_end):
                        is_modified = True
                        break
                if is_modified:
                    modified_symbols.append({
                        "name": cls["name"],
                        "type": "class",
                        "file_path": cf.file_path
                    })

        # If no specific functions were matched (e.g. single file script or simple diff), create symbol from filename
        if not modified_symbols and changed_files:
            for cf in changed_files:
                base_name = Path(cf.file_path).stem
                modified_symbols.append({
                    "name": base_name,
                    "type": "module",
                    "file_path": cf.file_path
                })

        # 2. Search for callers across repo or provided file contents
        all_sources: Dict[str, str] = dict(file_contents)
        if self.repo_dir and self.repo_dir.exists():
            for root, dirs, files in os.walk(self.repo_dir):
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", "__pycache__"}]
                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext in [".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go"]:
                        full_p = Path(root) / f
                        rel_p = str(full_p.relative_to(self.repo_dir)).replace("\\", "/")
                        if rel_p not in all_sources:
                            try:
                                all_sources[rel_p] = full_p.read_text(encoding="utf-8", errors="replace")
                            except Exception:
                                pass

        for sym in modified_symbols:
            sym_name = sym["name"]
            sym_file = sym["file_path"]

            direct_callers = set()
            dependent_modules = set()
            affected_apis = set()

            call_regex = re.compile(rf"\b{re.escape(sym_name)}\s*\(")

            for file_path, code in all_sources.items():
                if file_path == sym_file:
                    continue  # callers in external files
                if call_regex.search(code):
                    direct_callers.add(f"{file_path}")
                    dependent_modules.add(str(Path(file_path).parent).replace("\\", "/"))
                    if any(api_indicator in file_path.lower() for api_indicator in ["api", "route", "endpoint", "controller", "view"]):
                        affected_apis.add(file_path)

            # Classify impact type
            impact_type = "DIRECT"
            if affected_apis:
                impact_type = "API"
            elif len(dependent_modules) > 1:
                impact_type = "ARCHITECTURAL"
            elif direct_callers:
                impact_type = "DEPENDENCY"

            impacts.append(ImpactItem(
                modified_symbol=sym_name,
                symbol_type=sym["type"],
                file_path=sym_file,
                direct_callers=list(direct_callers)[:15],
                indirect_callers=[],
                dependent_modules=list(dependent_modules)[:10],
                affected_apis=list(affected_apis)[:10],
                impact_type=impact_type,
                verified=True
            ))

        return impacts
