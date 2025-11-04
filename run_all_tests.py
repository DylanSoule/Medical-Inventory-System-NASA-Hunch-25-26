import subprocess
import sys
import os

def install_requirements():
    """Install all dependencies listed in requirements file."""
    req_file = "requirements"
    if os.path.exists(req_file):
        print(f"Installing dependencies from {req_file}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
    else:
        print("No requirements file found — skipping dependency installation.")

def run_pytests():
    """Run pytest on all test_*.py files."""
    print("\n=== Running Tests ===\n")
    result = subprocess.run(["pytest", "-v"], check=False)
    if result.returncode == 0:
        print("\n✅ All tests passed successfully!")
    else:
        print("\n❌ Some tests failed. Check above for details.")
    sys.exit(result.returncode)
