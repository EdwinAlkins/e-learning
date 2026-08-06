import sys
import json
import tomllib
import urllib.request
from typing import Dict, Tuple
import re
from typing import Tuple


PYPI_URL = "https://pypi.org/pypi/{}/json"

# alias type result: { "group_name": { "dependency_name": { "used": "version", "latest": "version" } } }
TypeResult = Dict[str, Dict[str, Dict[str, str]]]


DEP_RE = re.compile(
    r"""
    ^
    (?P<name>[A-Za-z0-9_.-]+)      # nom du package
    (?:\[[^\]]+\])?                # extras optionnels
    (?P<spec>.*)?                  # contraintes de version
    $
    """,
    re.VERBOSE,
)


def parse_dependency(dep: str) -> Tuple[str, str]:
    """
    Exemples:
    - fastapi>=0.100        -> ("fastapi", ">=0.100")
    - requests             -> ("requests", "unknown")
    - uvicorn[standard]    -> ("uvicorn", "unknown")
    - pytest~=8.0          -> ("pytest", "~=8.0")
    """
    match = DEP_RE.match(dep.strip())
    if not match:
        return dep, "unknown"

    name = match.group("name")
    spec = match.group("spec") or ""

    spec = spec.strip()
    if not spec:
        spec = "unknown"

    return name, spec


def load_pyproject(path: str) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def get_latest_version(package: str) -> str:
    try:
        with urllib.request.urlopen(PYPI_URL.format(package), timeout=5) as r:
            data = json.load(r)
            return data["info"]["version"]
    except Exception:
        return "unknown"


def extract_dependencies(pyproject: dict) -> TypeResult:
    result: TypeResult = {}

    project = pyproject.get("project", {})
    
    result["main"] = {}

    # main dependencies
    for dep in project.get("dependencies", []) or []:
        name, used = parse_dependency(dep)
        result["main"][name] = {
            "used": used,
            "latest": get_latest_version(name),
        }

    # dependency-groups.dev
    dep_groups = pyproject.get("dependency-groups", {})
    for group_name, deps in dep_groups.items():
        result[group_name] = {}
        for dep in deps or []:
            name, used = parse_dependency(dep)
            result[group_name][name] = {
                "used": used,
                "latest": get_latest_version(name),
            }


    return result


def main():
    if len(sys.argv) != 2:
        print("Usage: python check_deps.py pyproject.toml")
        sys.exit(1)

    pyproject_path = sys.argv[1]
    pyproject = load_pyproject(pyproject_path)

    deps = extract_dependencies(pyproject)

    print(f"{'DEPENDENCY':25} {'USED':20} {'LATEST'}")
    print("-" * 60)

    for group_name, deps in sorted(deps.items()):
        print(f"{group_name:25}")
        for name, info in sorted(deps.items()):
            print(f"{name:25} {info['used']:20} {info['latest']}")
        print()


if __name__ == "__main__":
    main()
