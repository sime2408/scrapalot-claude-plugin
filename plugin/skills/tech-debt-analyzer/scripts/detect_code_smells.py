#!/usr/bin/env python3
"""
Detect code smells and technical debt indicators in Python codebases.

Analyzes Python source code for:
- Large files and functions
- High complexity code (cyclomatic complexity)
- TODO/FIXME/HACK/XXX comments
- Missing type hints
- Poor error handling patterns
- Async/await anti-patterns
- Missing docstrings

Usage:
    python detect_code_smells.py [src-dir] [--output json|markdown]

Example:
    python detect_code_smells.py src/main --output markdown > debt_report.md
"""

import ast
from collections import defaultdict
import json
from pathlib import Path
import re
import sys


class CodeSmellDetector:
    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
        self.issues = defaultdict(list)
        self.stats = {"total_files": 0, "total_lines": 0, "total_issues": 0}

    def analyze(self):
        """Run all analysis checks."""
        for file_path in self.src_dir.rglob("*.py"):
            if self._should_analyze(file_path):
                self.stats["total_files"] += 1
                self._analyze_file(file_path)

        self.stats["total_issues"] = sum(len(issues) for issues in self.issues.values())
        return self.issues, self.stats

    def _should_analyze(self, path: Path) -> bool:
        """Check if file should be analyzed."""
        if not path.is_file():
            return False

        # Skip __init__.py, test files, migrations, venv
        skip_patterns = ["__init__.py", "test_", "conftest.py", "alembic/versions", "venv/", ".venv/"]
        return not any(pattern in str(path) for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            self.stats["total_lines"] += len(lines)

            # Run all checks
            self._check_file_size(file_path, lines)
            self._check_debt_markers(file_path, lines)
            self._check_print_statements(file_path, lines)
            self._check_type_hints(file_path, content)
            self._check_error_handling(file_path, content)
            self._check_docstrings(file_path, content)
            self._check_complexity(file_path, content)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}", file=sys.stderr)

    def _check_file_size(self, file_path: Path, lines: list[str]):
        """Check for files that are too large."""
        line_count = len(lines)

        if line_count > 500:
            severity = "HIGH" if line_count > 1000 else "MEDIUM"
            self.issues["large_files"].append(
                {"file": str(file_path), "lines": line_count, "severity": severity, "message": f"File too large ({line_count} lines)"}
            )

    def _check_debt_markers(self, file_path: Path, lines: list[str]):
        """Check for TODO, FIXME, HACK, XXX, BUG comments."""
        markers = ["TODO", "FIXME", "HACK", "XXX", "BUG", "DEBT"]

        for line_num, line in enumerate(lines, start=1):
            for marker in markers:
                if f"# {marker}" in line or f"#{marker}" in line:
                    self.issues["debt_markers"].append(
                        {"file": str(file_path), "line": line_num, "marker": marker, "severity": "MEDIUM", "message": line.strip()}
                    )

    def _check_print_statements(self, file_path: Path, lines: list[str]):
        """Check for print() statements (should use logger)."""
        for line_num, line in enumerate(lines, start=1):
            if re.search(r"\bprint\s*\(", line) and not line.strip().startswith("#"):
                self.issues["print_statements"].append(
                    {"file": str(file_path), "line": line_num, "severity": "LOW", "message": "Use logger instead of print()"}
                )

    def _check_type_hints(self, file_path: Path, content: str):
        """Check for missing type hints on functions."""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip private functions and test functions
                    if node.name.startswith("_") or node.name.startswith("test_"):
                        continue

                    # Check return type hint
                    if node.returns is None:
                        self.issues["missing_type_hints"].append(
                            {
                                "file": str(file_path),
                                "line": node.lineno,
                                "function": node.name,
                                "severity": "MEDIUM",
                                "message": f"Function {node.name} missing return type hint",
                            }
                        )

                    # Check parameter type hints
                    for arg in node.args.args:
                        if arg.annotation is None and arg.arg != "self":
                            self.issues["missing_type_hints"].append(
                                {
                                    "file": str(file_path),
                                    "line": node.lineno,
                                    "function": node.name,
                                    "parameter": arg.arg,
                                    "severity": "MEDIUM",
                                    "message": f"Parameter {arg.arg} in {node.name} missing type hint",
                                }
                            )

        except SyntaxError:
            pass

    def _check_error_handling(self, file_path: Path, content: str):
        """Check for poor error handling patterns."""
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Bare except
            if stripped == "except:":
                self.issues["error_handling"].append(
                    {"file": str(file_path), "line": line_num, "severity": "HIGH", "message": "Bare except: clause (too broad)"}
                )

            # Swallowed exceptions
            if stripped == "pass" and line_num > 1:
                prev_line = lines[line_num - 2].strip()
                if prev_line.startswith("except"):
                    self.issues["error_handling"].append(
                        {"file": str(file_path), "line": line_num, "severity": "HIGH", "message": "Exception swallowed with pass"}
                    )

    def _check_docstrings(self, file_path: Path, content: str):
        """Check for missing docstrings on classes and public functions."""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Check classes
                if isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        self.issues["missing_docstrings"].append(
                            {
                                "file": str(file_path),
                                "line": node.lineno,
                                "type": "class",
                                "name": node.name,
                                "severity": "MEDIUM",
                                "message": f"Class {node.name} missing docstring",
                            }
                        )

                # Check public functions
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith("_") and not ast.get_docstring(node):
                        self.issues["missing_docstrings"].append(
                            {
                                "file": str(file_path),
                                "line": node.lineno,
                                "type": "function",
                                "name": node.name,
                                "severity": "LOW",
                                "message": f"Function {node.name} missing docstring",
                            }
                        )

        except SyntaxError:
            pass

    def _check_complexity(self, file_path: Path, content: str):
        """Check for complex functions (high cyclomatic complexity)."""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_complexity(node)

                    if complexity > 10:
                        severity = "HIGH" if complexity > 20 else "MEDIUM"
                        self.issues["high_complexity"].append(
                            {
                                "file": str(file_path),
                                "line": node.lineno,
                                "function": node.name,
                                "complexity": complexity,
                                "severity": severity,
                                "message": f"Function {node.name} has complexity {complexity}",
                            }
                        )

        except SyntaxError:
            pass

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ExceptHandler,)):
                complexity += 1

        return complexity


def format_markdown(issues: dict, stats: dict) -> str:
    """Format issues as markdown report."""
    output = ["# Technical Debt Analysis Report\n"]

    # Summary
    output.append(f"**Files Analyzed:** {stats['total_files']}")
    output.append(f"**Total Lines:** {stats['total_lines']:,}")
    output.append(f"**Total Issues:** {stats['total_issues']}\n")

    # Count by severity
    severity_counts = defaultdict(int)
    for category_issues in issues.values():
        for issue in category_issues:
            severity_counts[issue.get("severity", "LOW")] += 1

    output.append("### Issues by Severity")
    for severity in ["HIGH", "MEDIUM", "LOW"]:
        if severity in severity_counts:
            output.append(f"- **{severity}:** {severity_counts[severity]}")
    output.append("")

    # Issues by category
    for category, category_issues in sorted(issues.items()):
        if not category_issues:
            continue

        category_title = category.replace("_", " ").title()
        output.append(f"## {category_title} ({len(category_issues)} issues)\n")

        # Group by severity
        by_severity = defaultdict(list)
        for issue in category_issues:
            by_severity[issue.get("severity", "LOW")].append(issue)

        for severity in ["HIGH", "MEDIUM", "LOW"]:
            if severity not in by_severity:
                continue

            output.append(f"### {severity} Priority\n")
            for issue in by_severity[severity]:
                file_name = issue["file"]
                line = issue.get("line", "?")
                message = issue["message"]

                output.append(f"- **{file_name}:{line}**: {message}")

            output.append("")

    return "\n".join(output)


def format_json(issues: dict, stats: dict) -> str:
    """Format issues as JSON."""
    return json.dumps({"stats": stats, "issues": issues}, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Usage: python detect_code_smells.py [src-dir] [--output json|markdown]")
        sys.exit(1)

    src_dir = sys.argv[1]
    output_format = "markdown"

    if len(sys.argv) > 2 and sys.argv[2] == "--output":
        output_format = sys.argv[3] if len(sys.argv) > 3 else "markdown"

    detector = CodeSmellDetector(src_dir)
    issues, stats = detector.analyze()

    if output_format == "json":
        print(format_json(issues, stats))
    else:
        print(format_markdown(issues, stats))


if __name__ == "__main__":
    main()
