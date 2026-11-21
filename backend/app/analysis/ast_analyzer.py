import ast
import re
from typing import List, Dict, Any, Optional

class ASTAnalyzer:
    """
    Parses source code into AST or regex-based symbol tables to extract
    functions, classes, calls, imports, and method signatures.
    """

    @staticmethod
    def analyze_python_code(code: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extracts AST symbols from Python code.
        """
        functions = []
        classes = []
        imports = []
        calls = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fall back to regex if Python code has syntax errors or partial snippet
            return ASTAnalyzer.analyze_polyglot_code(code, file_path)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                functions.append({
                    "name": node.name,
                    "type": "function",
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno + 1),
                    "args": args,
                    "docstring": ast.get_docstring(node) or "",
                    "file_path": file_path
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "type": "class",
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno + 1),
                    "bases": [b.id for b in node.bases if isinstance(b, ast.Name)],
                    "file_path": file_path
                })
            elif isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    imports.append(f"{module}.{name.name}" if module else name.name)
            elif isinstance(node, ast.Call):
                call_name = ""
                if isinstance(node.func, ast.Name):
                    call_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    call_name = node.func.attr
                if call_name:
                    calls.append({
                        "name": call_name,
                        "line": node.lineno,
                        "file_path": file_path
                    })

        return {
            "functions": functions,
            "classes": classes,
            "imports": list(set(imports)),
            "calls": calls
        }

    @staticmethod
    def analyze_polyglot_code(code: str, file_path: str = "") -> Dict[str, Any]:
        """
        Regex-based parser for JavaScript, TypeScript, Java, Go, and C/C++.
        """
        functions = []
        classes = []
        imports = []
        calls = []

        lines = code.splitlines()

        # Function patterns: function foo(...) or const foo = (...) => or def foo(...)
        fn_pattern = re.compile(r"""(?:(?:function|def|async function)\s+([a-zA-Z0-9_$]+)|(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|(?:public|private|protected|static|\s)+[a-zA-Z0-9_<>[\]]+\s+([a-zA-Z0-9_$]+)\s*\([^)]*\)\s*\{)""")
        # Class patterns
        class_pattern = re.compile(r"""(?:class|interface|struct)\s+([a-zA-Z0-9_$]+)""")
        # Import patterns
        import_pattern = re.compile(r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\(['"]([^'"]+)['"]\)|import\s+([a-zA-Z0-9_.*]+))""")
        # Call patterns
        call_pattern = re.compile(r"""([a-zA-Z0-9_$]+)\s*\(""")

        for idx, line in enumerate(lines, 1):
            fn_match = fn_pattern.search(line)
            if fn_match:
                name = fn_match.group(1) or fn_match.group(2) or fn_match.group(3)
                if name and name not in ("if", "for", "while", "switch", "catch"):
                    functions.append({
                        "name": name,
                        "type": "function",
                        "line_start": idx,
                        "line_end": idx + 10,
                        "args": [],
                        "file_path": file_path
                    })

            class_match = class_pattern.search(line)
            if class_match:
                classes.append({
                    "name": class_match.group(1),
                    "type": "class",
                    "line_start": idx,
                    "line_end": idx + 25,
                    "file_path": file_path
                })

            for imp_match in import_pattern.finditer(line):
                imp = imp_match.group(1) or imp_match.group(2) or imp_match.group(3)
                if imp:
                    imports.append(imp)

            for c_match in call_pattern.finditer(line):
                cname = c_match.group(1)
                if cname not in ("if", "for", "while", "switch", "catch", "return", "function", "def", "typeof"):
                    calls.append({
                        "name": cname,
                        "line": idx,
                        "file_path": file_path
                    })

        return {
            "functions": functions,
            "classes": classes,
            "imports": list(set(imports)),
            "calls": calls
        }
