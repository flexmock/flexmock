#!/usr/bin/env python3
"""Prepare, release and verify flexmock versions.

The version is stored in pyproject.toml and setup.py, and each release has a section in
CHANGELOG.md. This script keeps those in sync. See CONTRIBUTING.md for the release process.
"""

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
SETUP_PY = ROOT / "setup.py"
CHANGELOG = ROOT / "CHANGELOG.md"
VERSION_FILES = [PYPROJECT, SETUP_PY, CHANGELOG]
MAIN_BRANCH = "master"
GITHUB_REPO = "flexmock/flexmock"
ORIGIN_URL = re.compile(rf"(?:git@github\.com:|https://github\.com/){GITHUB_REPO}(?:\.git)?")

PYPROJECT_VERSION = re.compile(r'^version = "(.+)"$', re.MULTILINE)
SETUP_PY_VERSION = re.compile(r'^VERSION = "(.+)"$', re.MULTILINE)
UNRELEASED = "## Unreleased"
# Older changelog entries contain other level two headings, so match release headings only.
SECTION_BOUNDARY = re.compile(r"^## (?:Unreleased|Release )", re.MULTILINE)


def read_version(path: Path, pattern: re.Pattern[str]) -> str:
    """Read the version from a file."""
    match = pattern.search(path.read_text(encoding="utf-8"))
    if match is None:
        raise SystemExit(f"Version not found in {path.name}.")
    return match.group(1)


def write_version(path: Path, pattern: re.Pattern[str], line: str) -> None:
    """Replace the version line in a file."""
    text = path.read_text(encoding="utf-8")
    path.write_text(pattern.sub(line, text, count=1), encoding="utf-8")


def changelog_section(heading: str) -> str:
    """Return the body of a changelog section, excluding the heading."""
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(heading)}$", text, re.MULTILINE)
    if match is None:
        raise SystemExit(f"Section '{heading}' not found in {CHANGELOG.name}.")
    boundary = SECTION_BOUNDARY.search(text, match.end())
    end = boundary.start() if boundary else len(text)
    return text[match.end() : end].strip()


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse a X.Y.Z version into a tuple of integers."""
    match = re.fullmatch(r"([0-9]+)\.([0-9]+)\.([0-9]+)", version)
    if match is None:
        raise SystemExit(f"Invalid version '{version}'. Expected format: X.Y.Z")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def next_version(current: str, bump: str) -> str:
    """Return the version that follows the current version for the given bump."""
    major, minor, patch = parse_version(current)
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def run(*args: str) -> str:
    """Run a command in the repository root and return its standard output."""
    return subprocess.run(
        args, cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE
    ).stdout.strip()


def confirm(question: str) -> bool:
    """Ask the user a yes or no question."""
    try:
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def ensure_gh_authenticated() -> None:
    """Check that GitHub CLI is installed and logged in."""
    try:
        subprocess.run(
            ["gh", "auth", "status", "--hostname", "github.com"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as error:
        raise SystemExit("GitHub CLI (gh) is not installed.") from error
    except subprocess.CalledProcessError as error:
        raise SystemExit("GitHub CLI is not logged in. Run: gh auth login") from error


def ensure_clean_main_branch() -> str:
    """Check that the main branch is checked out, clean and up to date, and return HEAD."""
    origin = run("git", "config", "--get", "remote.origin.url")
    if not ORIGIN_URL.fullmatch(origin):
        raise SystemExit(f"Remote 'origin' must be {GITHUB_REPO} on GitHub (is '{origin}').")
    branch = run("git", "branch", "--show-current")
    if branch != MAIN_BRANCH:
        raise SystemExit(f"Check out the '{MAIN_BRANCH}' branch first (currently on '{branch}').")
    if run("git", "status", "--porcelain"):
        raise SystemExit("The working tree has uncommitted changes.")
    run("git", "fetch", "--quiet", "origin", MAIN_BRANCH)
    head = run("git", "rev-parse", "HEAD")
    if head != run("git", "rev-parse", f"refs/remotes/origin/{MAIN_BRANCH}"):
        raise SystemExit(f"Local '{MAIN_BRANCH}' is not in sync with 'origin/{MAIN_BRANCH}'.")
    return head


def check(tag: str | None) -> str:
    """Verify that the version files, the changelog and the optional release tag agree."""
    version = read_version(PYPROJECT, PYPROJECT_VERSION)
    parse_version(version)
    setup_py_version = read_version(SETUP_PY, SETUP_PY_VERSION)
    if setup_py_version != version:
        raise SystemExit(
            f"Version mismatch: pyproject.toml has {version}, setup.py has {setup_py_version}."
        )
    if tag is not None and tag != f"v{version}":
        raise SystemExit(f"Version mismatch: release tag is {tag}, expected v{version}.")
    if not changelog_section(f"## Release {version}"):
        raise SystemExit(f"Section '## Release {version}' in {CHANGELOG.name} is empty.")
    print(f"Release metadata is consistent for version {version}.")
    return version


def prepare(bump: str) -> None:
    """Bump the version, update the changelog and open a pull request with the changes."""
    ensure_clean_main_branch()
    ensure_gh_authenticated()
    current = read_version(PYPROJECT, PYPROJECT_VERSION)
    version = next_version(current, bump)
    branch = f"release-{version}"
    if not changelog_section(UNRELEASED):
        raise SystemExit(f"Section '{UNRELEASED}' in {CHANGELOG.name} is empty.")
    if run("git", "branch", "--list", branch) or run(
        "git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}"
    ):
        raise SystemExit(f"Branch '{branch}' already exists.")

    print(f"Bumping version: {current} -> {version}")
    write_version(PYPROJECT, PYPROJECT_VERSION, f'version = "{version}"')
    write_version(SETUP_PY, SETUP_PY_VERSION, f'VERSION = "{version}"')
    text = CHANGELOG.read_text(encoding="utf-8")
    text = text.replace(UNRELEASED, f"{UNRELEASED}\n\n## Release {version}", 1)
    CHANGELOG.write_text(text, encoding="utf-8")
    subprocess.run(["git", "--no-pager", "diff"], cwd=ROOT, check=True)

    if not confirm(f"\nCommit to branch '{branch}', push it and open a pull request?"):
        revert_prepare(branch)
        raise SystemExit("Aborted. The changes were reverted.")

    try:
        run("git", "switch", "--create", branch)
        run("git", "commit", "--message", f"Release {version}", "--", *map(str, VERSION_FILES))
    except (subprocess.CalledProcessError, KeyboardInterrupt) as error:
        revert_prepare(branch)
        raise SystemExit("Committing failed. The changes were reverted.") from error

    pr_command = [
        "gh", "pr", "create", "--repo", GITHUB_REPO, "--base", MAIN_BRANCH, "--head", branch,
        "--title", f"Release {version}", "--body", changelog_section(f"## Release {version}"),
    ]  # fmt: skip
    push = subprocess.run(
        ["git", "push", "--set-upstream", "origin", f"refs/heads/{branch}:refs/heads/{branch}"],
        cwd=ROOT,
        check=False,
    )
    if push.returncode != 0:
        raise SystemExit(
            f"Pushing failed. The release commit is on the local branch '{branch}'. Retry with\n"
            f"  git push --set-upstream origin {branch}\n"
            f"and open the pull request with\n  gh pr create --repo {GITHUB_REPO} --fill\n"
            f"or remove the branch with\n"
            f"  git switch {MAIN_BRANCH}; git branch --delete --force {branch}"
        )
    if subprocess.run(pr_command, cwd=ROOT, check=False).returncode != 0:
        raise SystemExit(
            f"Opening the pull request failed. The branch '{branch}' is pushed. Open the pull "
            f"request with\n  gh pr create --repo {GITHUB_REPO} --fill"
        )
    print("\nAfter the pull request is approved and merged, run: release.py release")


def revert_prepare(branch: str) -> None:
    """Revert the changes of an unfinished prepare and return to the main branch."""
    files = [str(path) for path in VERSION_FILES]
    for command in (
        ["git", "checkout", "--", *files],
        ["git", "switch", MAIN_BRANCH],
        ["git", "branch", "--delete", branch],
    ):
        subprocess.run(command, cwd=ROOT, check=False, capture_output=True)


def release() -> None:
    """Create the GitHub release for the version on the main branch."""
    head = ensure_clean_main_branch()
    ensure_gh_authenticated()
    version = check(None)
    tag = f"v{version}"
    if run("git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"):
        raise SystemExit(f"Tag {tag} already exists. Prepare a new version first.")

    notes = changelog_section(f"## Release {version}")
    print(f"\nRelease notes for {tag}:\n\n{notes}\n")
    if not confirm(f"Create GitHub release {tag} at commit {head}? This starts publishing."):
        raise SystemExit("Aborted.")
    subprocess.run(
        ["gh", "release", "create", tag, "--repo", GITHUB_REPO, "--target", head]
        + ["--title", tag, "--notes", notes],
        cwd=ROOT,
        check=True,
    )
    print("\nApprove the deployment in the publish workflow run to upload the release to PyPI.")


def main() -> None:
    """Run the command given on the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    prepare_parser = commands.add_parser(
        "prepare", help="bump version, update changelog and open a pull request"
    )
    prepare_parser.add_argument(
        "bump", choices=["major", "minor", "patch"], help="version part to bump"
    )
    commands.add_parser("release", help="create the GitHub release after the pull request")
    check_parser = commands.add_parser("check", help="verify version files and changelog")
    check_parser.add_argument("--tag", help="release tag to verify, for example v1.2.3")

    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare(args.bump)
        elif args.command == "release":
            release()
        else:
            check(args.tag)
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"Command failed: {' '.join(map(str, error.cmd))}") from error


if __name__ == "__main__":
    main()
