"""
Tests that the declared dependencies match what the package actually imports.

Unused dependencies are not merely untidy: numpy and pandas are roughly 100 MB of
compiled wheels, which matters against the 250 MB unzipped AWS Lambda layer limit.
"""

import ast
import pathlib
import unittest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE_ROOT = REPO_ROOT / "nost_tools"
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Distribution name -> module name, where they differ
DISTRIBUTION_MODULES = {
    "pyyaml": "yaml",
    "python-dotenv": "dotenv",
    "python-keycloak": "keycloak",
    "python-dateutil": "dateutil",
    "pydantic": "pydantic",
    "pika": "pika",
    "ntplib": "ntplib",
    "numpy": "numpy",
    "pandas": "pandas",
}


def imported_modules(root):
    """Top-level modules imported by every Python file under root."""
    modules = set()
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.add(node.module.split(".")[0])
    return modules


def declared(section):
    """Requirement names from a pyproject dependency list, lowercased."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    if section == "core":
        requirements = data["project"]["dependencies"]
    else:
        requirements = data["project"]["optional-dependencies"][section]
    names = []
    for requirement in requirements:
        name = requirement.split(">")[0].split("<")[0].split("=")[0].split("[")[0]
        names.append(name.strip().lower())
    return names


@unittest.skipIf(tomllib is None, "tomllib requires Python 3.11 or later")
class TestCoreDependencies(unittest.TestCase):
    def test_every_core_dependency_is_imported_by_the_package(self):
        imports = imported_modules(PACKAGE_ROOT)
        unused = [
            name
            for name in declared("core")
            if DISTRIBUTION_MODULES.get(name, name) not in imports
        ]
        self.assertEqual(
            unused,
            [],
            f"declared but never imported by nost_tools: {unused}. "
            "Move to an optional extra if only the examples need them.",
        )

    def test_heavy_scientific_packages_are_not_core_dependencies(self):
        """
        numpy and pandas belong to the examples, not the library. Keeping them
        out of the core install keeps Lambda layer builds within the size limit.
        """
        core = declared("core")
        for package in ("numpy", "pandas"):
            self.assertNotIn(package, core)

    def test_examples_extra_provides_what_the_examples_import(self):
        extra = declared("examples")
        for package in ("numpy", "pandas"):
            self.assertIn(
                package,
                extra,
                f"{package} is imported by the examples but not declared in the "
                "examples extra",
            )


if __name__ == "__main__":
    unittest.main()
