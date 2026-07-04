# scripts/package_submission.py
import os
import zipfile
from pathlib import Path

def package_project(output_filename: str = "submission.zip"):
    """Cleans up cache files and packages the workspace into a clean submission zip file."""
    workspace_dir = Path(__file__).parent.parent.resolve()
    print(f"[Architect] Initiating packaging script in workspace: {workspace_dir}")
    
    # Files/folders to exclude from submission zip
    ignore_patterns = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".env",
        "submission.zip",
        ".DS_Store",
        ".agents",
        ".gemini",
        "uv.lock"
    }

    ignored_extensions = {".pyc", ".pyo", ".pyd"}

    zip_path = workspace_dir / output_filename
    print(f"[Developer] Creating zip package at: {zip_path}")

    files_zipped = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(workspace_dir):
            # Exclude folders matches
            dirs[:] = [d for d in dirs if d not in ignore_patterns and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(workspace_dir)

                # Skip ignored files
                if file in ignore_patterns or file_path.suffix in ignored_extensions:
                    continue
                if any(part.startswith(".") for part in relative_path.parts):
                    continue

                zip_file.write(file_path, relative_path)
                files_zipped += 1

    print(f"[Security Auditor] Finished packaging. Zipped {files_zipped} files successfully.")
    print(f"[Success] Project packaged cleanly into: {output_filename}")

if __name__ == "__main__":
    package_project()
