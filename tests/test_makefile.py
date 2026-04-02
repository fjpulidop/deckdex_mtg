"""Tests for the root-level Makefile structure and target declarations.

These tests verify:
- The Makefile exists at the project root.
- All documented targets are declared as .PHONY.
- The VENV_GUARD and PYTHON_GUARD macros are present.
- `.venv/` is excluded from git tracking via .gitignore.
- Every documented target appears as a recipe name in the file.
- `make --dry-run <target>` exits 0 for all targets (syntax / parse check).
"""

import os
import re
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAKEFILE_PATH = os.path.join(REPO_ROOT, "Makefile")
GITIGNORE_PATH = os.path.join(REPO_ROOT, ".gitignore")

# All targets documented in the Makefile header comment.
EXPECTED_TARGETS = [
    "install",
    "dev",
    "backend",
    "frontend",
    "test",
    "db-setup",
    "docker-up",
    "docker-down",
    "clean",
    "help",
]


def _read_makefile() -> str:
    with open(MAKEFILE_PATH) as fh:
        return fh.read()


class TestMakefileExists:
    def test_makefile_is_present(self):
        assert os.path.isfile(MAKEFILE_PATH), "Makefile not found at project root"

    def test_makefile_is_non_empty(self):
        assert os.path.getsize(MAKEFILE_PATH) > 0, "Makefile is empty"


class TestPhonyDeclaration:
    def test_phony_line_exists(self):
        content = _read_makefile()
        assert ".PHONY:" in content, ".PHONY declaration not found in Makefile"

    def test_all_targets_declared_phony(self):
        content = _read_makefile()
        # Collect all tokens listed after .PHONY:
        phony_match = re.search(r"^\.PHONY:\s*(.+)$", content, re.MULTILINE)
        assert phony_match, ".PHONY line could not be parsed"
        phony_targets = set(phony_match.group(1).split())
        missing = [t for t in EXPECTED_TARGETS if t not in phony_targets]
        assert not missing, f"Targets not in .PHONY: {missing}"


class TestRecipePresence:
    """Each expected target must appear as a recipe header (target:) in the Makefile."""

    def test_all_targets_have_recipes(self):
        content = _read_makefile()
        missing = []
        for target in EXPECTED_TARGETS:
            # Match a recipe header: target name at start of line followed by ':'
            # and optionally more deps (not an assignment).
            pattern = rf"^{re.escape(target)}\s*:"
            if not re.search(pattern, content, re.MULTILINE):
                missing.append(target)
        assert not missing, f"Targets without recipes: {missing}"


class TestGuardMacros:
    def test_venv_guard_defined(self):
        content = _read_makefile()
        assert "define VENV_GUARD" in content, "VENV_GUARD macro not defined"

    def test_python_guard_defined(self):
        content = _read_makefile()
        assert "define PYTHON_GUARD" in content, "PYTHON_GUARD macro not defined"

    def test_venv_guard_checks_python_binary(self):
        """VENV_GUARD should gate on the venv Python binary existing."""
        content = _read_makefile()
        guard_block = re.search(r"define VENV_GUARD(.+?)endef", content, re.DOTALL)
        assert guard_block, "VENV_GUARD block could not be extracted"
        assert "$(PYTHON)" in guard_block.group(1), "VENV_GUARD does not reference $(PYTHON)"


class TestVariableDeclarations:
    def test_venv_variable_set(self):
        content = _read_makefile()
        assert re.search(r"^VENV\s*:=", content, re.MULTILINE), "VENV variable not declared"

    def test_python_variable_set(self):
        content = _read_makefile()
        assert re.search(r"^PYTHON\s*:=", content, re.MULTILINE), "PYTHON variable not declared"

    def test_frontend_dir_variable_set(self):
        content = _read_makefile()
        assert re.search(r"^FRONTEND_DIR\s*:=", content, re.MULTILINE), "FRONTEND_DIR variable not declared"

    def test_default_goal_is_help(self):
        content = _read_makefile()
        assert re.search(r"^\.DEFAULT_GOAL\s*:=\s*help", content, re.MULTILINE), ".DEFAULT_GOAL should be 'help'"


class TestGitignore:
    def test_venv_excluded_in_gitignore(self):
        assert os.path.isfile(GITIGNORE_PATH), ".gitignore not found"
        with open(GITIGNORE_PATH) as fh:
            entries = [line.strip() for line in fh if line.strip()]
        # Accept bare '.venv' or '.venv/' as valid forms.
        matches = [e for e in entries if e in (".venv", ".venv/")]
        assert matches, ".venv not found in .gitignore"


class TestDryRun:
    """Verify `make --dry-run <target>` exits 0 for all targets.

    This is a lightweight Makefile parse/syntax check that does not execute
    any real commands (no pip install, no docker, etc.).
    """

    def _dry_run(self, target: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["make", "--dry-run", target],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def test_dry_run_help(self):
        result = self._dry_run("help")
        assert result.returncode == 0, f"make --dry-run help failed:\n{result.stderr}"

    def test_dry_run_install(self):
        result = self._dry_run("install")
        assert result.returncode == 0, f"make --dry-run install failed:\n{result.stderr}"

    def test_dry_run_backend(self):
        result = self._dry_run("backend")
        assert result.returncode == 0, f"make --dry-run backend failed:\n{result.stderr}"

    def test_dry_run_frontend(self):
        result = self._dry_run("frontend")
        assert result.returncode == 0, f"make --dry-run frontend failed:\n{result.stderr}"

    def test_dry_run_test(self):
        result = self._dry_run("test")
        assert result.returncode == 0, f"make --dry-run test failed:\n{result.stderr}"

    def test_dry_run_db_setup(self):
        result = self._dry_run("db-setup")
        assert result.returncode == 0, f"make --dry-run db-setup failed:\n{result.stderr}"

    def test_dry_run_docker_up(self):
        result = self._dry_run("docker-up")
        assert result.returncode == 0, f"make --dry-run docker-up failed:\n{result.stderr}"

    def test_dry_run_docker_down(self):
        result = self._dry_run("docker-down")
        assert result.returncode == 0, f"make --dry-run docker-down failed:\n{result.stderr}"

    def test_dry_run_clean(self):
        result = self._dry_run("clean")
        assert result.returncode == 0, f"make --dry-run clean failed:\n{result.stderr}"

    def test_dry_run_all_targets_produce_output(self):
        """Each target should print at least one command in dry-run mode."""
        for target in EXPECTED_TARGETS:
            result = self._dry_run(target)
            assert result.returncode == 0, f"make --dry-run {target} exited {result.returncode}:\n{result.stderr}"
            assert result.stdout.strip(), f"make --dry-run {target} produced no output — recipe may be empty"
