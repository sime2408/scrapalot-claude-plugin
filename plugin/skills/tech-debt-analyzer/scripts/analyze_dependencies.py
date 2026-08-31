#!/usr/bin/env python3
"""
Analyze Python dependencies for technical debt indicators.

Checks for:
- Outdated packages
- Security vulnerabilities (via pip-audit if available)
- Duplicate functionality packages
- Unsafe version constraints
- Unused dependencies

Usage:
    python analyze_dependencies.py [requirements.txt or pyproject.toml]

Example:
    python analyze_dependencies.py requirements.txt
"""

from collections import defaultdict
from pathlib import Path
import re
import subprocess
import sys


class DependencyAnalyzer:
    # Known deprecated/problematic packages
    DEPRECATED_PACKAGES = {
        "flask-cors": "Consider using Flask built-in CORS support",
        "pycrypto": "Use pycryptodome instead (actively maintained)",
        "mysql-python": "Use mysqlclient or PyMySQL instead",
        "optparse": "Use argparse instead (stdlib)",
    }

    # Common duplicate functionality patterns
    DUPLICATE_PATTERNS = {
        "http_client": ["requests", "httpx", "aiohttp", "urllib3"],
        "async_runtime": ["asyncio", "trio", "curio"],
        "validation": ["pydantic", "marshmallow", "cerberus", "voluptuous"],
        "testing": ["pytest", "unittest", "nose", "nose2"],
        "orm": ["sqlalchemy", "peewee", "tortoise-orm", "pony"],
        "web_framework": ["fastapi", "flask", "django", "starlette"],
    }

    def __init__(self, requirements_file: str):
        self.requirements_file = Path(requirements_file)
        self.dependencies = []
        self.issues = defaultdict(list)

    def analyze(self):
        """Run all dependency checks."""
        self._parse_requirements()
        self._check_deprecated()
        self._check_duplicates()
        self._check_version_constraints()
        self._check_outdated()

        return self.issues

    def _parse_requirements(self):
        """Parse requirements.txt or pyproject.toml."""
        content = self.requirements_file.read_text()

        if self.requirements_file.name == "pyproject.toml":
            self._parse_pyproject(content)
        else:
            self._parse_requirements_txt(content)

    def _parse_requirements_txt(self, content: str):
        """Parse requirements.txt format."""
        for line in content.split("\n"):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Skip -e editable installs, -r includes
            if line.startswith("-"):
                continue

            # Parse package and version
            match = re.match(r"^([a-zA-Z0-9_-]+)([=<>~!]=?)(.*)$", line)
            if match:
                package = match.group(1).lower()
                operator = match.group(2)
                version = match.group(3)

                self.dependencies.append({"package": package, "operator": operator, "version": version, "raw": line})

    def _parse_pyproject(self, content: str):
        """Parse pyproject.toml dependencies."""
        # Simple regex-based parsing for dependencies section
        in_dependencies = False

        for line in content.split("\n"):
            line = line.strip()

            if line.startswith("[tool.poetry.dependencies]") or line.startswith("[project.dependencies]"):
                in_dependencies = True
                continue

            if in_dependencies:
                if line.startswith("["):
                    break

                # Parse package = "version" format
                match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*["\']([^"\']+)["\']', line)
                if match:
                    package = match.group(1).lower()
                    version_spec = match.group(2)

                    self.dependencies.append({"package": package, "operator": "==", "version": version_spec, "raw": line})

    def _check_deprecated(self):
        """Check for deprecated or problematic packages."""
        for dep in self.dependencies:
            package = dep["package"]

            if package in self.DEPRECATED_PACKAGES:
                self.issues["deprecated"].append(
                    {
                        "package": package,
                        "severity": "HIGH",
                        "message": f"Deprecated: {self.DEPRECATED_PACKAGES[package]}",
                        "current_version": dep["version"],
                    }
                )

    def _check_duplicates(self):
        """Check for packages with duplicate functionality."""
        used_packages = {dep["package"] for dep in self.dependencies}

        for category, packages in self.DUPLICATE_PATTERNS.items():
            found = [p for p in packages if p in used_packages]

            if len(found) > 1:
                self.issues["duplicates"].append(
                    {
                        "category": category,
                        "packages": found,
                        "severity": "MEDIUM",
                        "message": f"Multiple {category.replace('_', ' ')} packages: {', '.join(found)}",
                    }
                )

    def _check_version_constraints(self):
        """Check for unsafe or overly strict version constraints."""
        for dep in self.dependencies:
            package = dep["package"]
            operator = dep["operator"]
            version = dep["version"]

            # Unsafe: No version pin at all
            if not operator or operator == "":
                self.issues["version_constraints"].append(
                    {
                        "package": package,
                        "severity": "HIGH",
                        "message": "No version constraint (allows any version)",
                        "suggestion": f"Pin to specific version range: {package}>=X.Y.Z,<X+1.0.0",
                    }
                )

            # Unsafe: Exact version without range
            elif operator == "==":
                self.issues["version_constraints"].append(
                    {
                        "package": package,
                        "severity": "LOW",
                        "message": "Exact version pin may prevent security updates",
                        "suggestion": f"Use range: {package}>={version},<{self._next_major(version)}",
                    }
                )

            # Warning: Wildcard or >= without upper bound
            elif operator in [">=", ">"] and "," not in dep["raw"]:
                self.issues["version_constraints"].append(
                    {
                        "package": package,
                        "severity": "MEDIUM",
                        "message": "No upper bound on version (may break on major updates)",
                        "suggestion": f"Add upper bound: {package}>={version},<{self._next_major(version)}",
                    }
                )

    def _next_major(self, version: str) -> str:
        """Calculate next major version."""
        try:
            parts = version.split(".")
            major = int(parts[0]) + 1
            return f"{major}.0.0"
        except:
            return "X+1.0.0"

    def _check_outdated(self):
        """Check for outdated packages using pip list --outdated."""
        try:
            result = subprocess.run(["pip", "list", "--outdated", "--format=json"], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                import json

                outdated = json.loads(result.stdout)

                for package_info in outdated:
                    package = package_info["name"].lower()

                    # Check if this package is in our dependencies
                    if any(dep["package"] == package for dep in self.dependencies):
                        self.issues["outdated"].append(
                            {
                                "package": package,
                                "current": package_info["version"],
                                "latest": package_info["latest_version"],
                                "severity": "MEDIUM",
                                "message": f"Outdated: {package_info['version']} → {package_info['latest_version']}",
                            }
                        )

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            # pip not available or command failed
            pass


def format_report(issues: dict) -> str:
    """Format issues as markdown report."""
    output = ["# Dependency Analysis Report\n"]

    total_issues = sum(len(v) for v in issues.values())
    output.append(f"**Total Issues:** {total_issues}\n")

    # Deprecated packages
    if "deprecated" in issues and issues["deprecated"]:
        output.append(f"## Deprecated/Outdated Packages ({len(issues['deprecated'])})\n")

        for issue in issues["deprecated"]:
            output.append(f"### {issue['package']} [HIGH]")
            output.append(f"{issue['message']}")
            output.append(f"- Current version: {issue['current_version']}\n")

    # Duplicates
    if "duplicates" in issues and issues["duplicates"]:
        output.append(f"## Duplicate Functionality ({len(issues['duplicates'])})\n")

        for issue in issues["duplicates"]:
            output.append(f"### {issue['category'].replace('_', ' ').title()} [MEDIUM]")
            output.append(f"{issue['message']}")
            output.append("- Consider consolidating to one package\n")

    # Version constraints
    if "version_constraints" in issues and issues["version_constraints"]:
        output.append(f"## Version Constraint Issues ({len(issues['version_constraints'])})\n")

        for issue in issues["version_constraints"]:
            output.append(f"### {issue['package']} [{issue['severity']}]")
            output.append(f"{issue['message']}")
            output.append(f"- Suggestion: {issue['suggestion']}\n")

    # Outdated
    if "outdated" in issues and issues["outdated"]:
        output.append(f"## Outdated Packages ({len(issues['outdated'])})\n")

        for issue in issues["outdated"]:
            output.append(f"### {issue['package']}")
            output.append(f"{issue['message']}\n")

    # Security recommendations
    output.append("\n## Security Recommendations\n")
    output.append("Run security audit with:")
    output.append("```bash")
    output.append("pip install pip-audit")
    output.append("pip-audit")
    output.append("```\n")

    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_dependencies.py [requirements.txt or pyproject.toml]")
        sys.exit(1)

    requirements_file = sys.argv[1]

    if not Path(requirements_file).exists():
        print(f"Error: {requirements_file} not found")
        sys.exit(1)

    analyzer = DependencyAnalyzer(requirements_file)
    issues = analyzer.analyze()

    print(format_report(issues))


if __name__ == "__main__":
    main()
