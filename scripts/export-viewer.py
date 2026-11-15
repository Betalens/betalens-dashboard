"""Explicitly copy a built, committed viewer into a core checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-dir", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    core = args.core_dir.expanduser().resolve()
    if not (core / "betalens/experiments/api.py").is_file():
        parser.error("--core-dir must point to a Betalens core checkout")
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
    if dirty.strip():
        parser.error("commit the UI source before exporting its build")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    bundle = root / "dist/experiment-viewer"
    if not (bundle / "index.html").is_file():
        parser.error("build both frontends first: cd dashboard/frontend && npm run build")
    files = sorted(path for path in bundle.rglob("*") if path.is_file())
    if any(path.is_symlink() for path in files):
        parser.error("viewer bundles cannot contain symbolic links")
    manifest = {
        "format": 1,
        "source_repository": "https://github.com/Janiszzz/betalens-dashboard",
        "source_commit": commit,
        "files": {path.relative_to(bundle).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
    }
    target = core / "betalens/experiments/web"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(bundle, target)
    (target / "viewer-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Exported {len(files)} viewer resources from {commit}")


if __name__ == "__main__":
    main()
