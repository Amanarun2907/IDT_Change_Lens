import pytest
from app.github.diff_engine import DiffEngine

def test_generate_manual_diff():
    orig = "def foo():\n    return 1\n"
    upd = "def foo():\n    return 2\n"
    diff = DiffEngine.generate_manual_diff(orig, upd, "foo.py")
    assert "--- a/foo.py" in diff
    assert "+++ b/foo.py" in diff
    assert "-    return 1" in diff
    assert "+    return 2" in diff

def test_normalize_raw_diff():
    raw = "--- a/bar.py\n+++ b/bar.py\n@@ -1,1 +1,1 @@\n-old\n+new"
    normalized = DiffEngine.normalize_diff_input(raw_diff=raw)
    assert normalized == raw

def test_parse_unified_diff():
    diff_text = """diff --git a/src/auth.py b/src/auth.py
index 1234567..89abcdef 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,3 +10,4 @@
 def authenticate(user):
-    return True
+    if not user:
+        return False
+    return True
"""
    files = DiffEngine.parse_unified_diff(diff_text)
    assert len(files) == 1
    assert files[0].file_path == "src/auth.py"
    assert files[0].additions == 3
    assert files[0].deletions == 1
    assert "authenticate" in files[0].diff_hunks

def test_extract_line_ranges():
    hunks = "@@ -10,5 +12,8 @@\n+line1\n+line2"
    ranges = DiffEngine.extract_line_ranges(hunks)
    assert len(ranges) == 1
    assert ranges[0]["start"] == 12
    assert ranges[0]["end"] == 19
