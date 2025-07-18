import re
import subprocess
from pathlib import Path
import argparse
import sys

PYPROJECT_PATH = Path("pyproject.toml")
REPO_URL = "https://github.com/NadavNV/SmartHomeValidation.git"
PACKAGE_NAME = "SmartHomeValidation"


def get_current_version():
    content = PYPROJECT_PATH.read_text()
    match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    return tuple(map(int, match.groups()))


def bump_version(version, part):
    major, minor, patch = version
    if part == "major":
        return major + 1, 0, 0
    elif part == "minor":
        return major, minor + 1, 0
    elif part == "patch":
        return major, minor, patch + 1
    else:
        raise ValueError("Unknown version part")


def update_pyproject(new_version):
    content = PYPROJECT_PATH.read_text()
    new_version_str = ".".join(map(str, new_version))
    content = re.sub(r'version\s*=\s*"\d+\.\d+\.\d+"',
                     f'version = "{new_version_str}"',
                     content)
    PYPROJECT_PATH.write_text(content)
    return new_version_str


def check_git_clean():
    result = subprocess.run(["git", "status", "--porcelain"], stdout=subprocess.PIPE, text=True)
    if result.stdout.strip():
        print("❌ Git working directory is not clean. Commit or stash changes first.")
        sys.exit(1)


def run_git_commands(new_version_str, dry_run=False):
    if dry_run:
        print(f"🧪 Would run: git add pyproject.toml")
        print(f"🧪 Would run: git commit -m 'Release version {new_version_str}'")
        print(f"🧪 Would run: git tag {new_version_str}")
        print(f"🧪 Would run: git push && git push origin {new_version_str}")
        return

    subprocess.run(["git", "add", "pyproject.toml"], check=True)
    subprocess.run(["git", "commit", "-m", f"Release version {new_version_str}"], check=True)
    subprocess.run(["git", "tag", new_version_str], check=True)
    subprocess.run(["git", "push"], check=True)
    subprocess.run(["git", "push", "origin", new_version_str], check=True)


def main():
    parser = argparse.ArgumentParser(description="Release a new version of SmartHomeValidation.")
    parser.add_argument("--part", choices=["major", "minor", "patch"], default="patch",
                        help="Which part of the version to bump.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen, don’t change anything.")
    args = parser.parse_args()

    print("🔍 Reading current version...")
    current = get_current_version()
    print(f"📦 Current version: {'.'.join(map(str, current))}")

    new_version = bump_version(current, part=args.part)
    new_version_str = ".".join(map(str, new_version))
    print(f"🚀 Bumping to: {new_version_str} ({args.part})")

    check_git_clean()

    if not args.dry_run:
        update_pyproject(new_version)
    else:
        print(f"🧪 Would update pyproject.toml to version = \"{new_version_str}\"")

    run_git_commands(new_version_str, dry_run=args.dry_run)

    print("\n✅ Release complete!" if not args.dry_run else "\n🧪 Dry run complete!")
    print("📌 Use this in requirements.txt:")
    print(f'{PACKAGE_NAME} @ git+{REPO_URL}@{new_version_str}')


if __name__ == "__main__":
    main()
