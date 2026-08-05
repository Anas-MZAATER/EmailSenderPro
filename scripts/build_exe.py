"""Build standalone executable with PyInstaller."""
import subprocess
import sys
from pathlib import Path


def build():
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    main_script = src_path / "emailsenderpro" / "app.py"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "EmailSenderPro",
        "--add-data", f"{src_path / 'emailsenderpro'};emailsenderpro",
        str(main_script),
    ]

    print("Building executable...")
    subprocess.run(cmd, cwd=project_root)
    print(f"Done! Check {project_root / 'dist' / 'EmailSenderPro.exe'}")


if __name__ == "__main__":
    build()
