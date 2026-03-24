# --- AUTO INSTALL WEBSOCKETS IF MISSING ---
import importlib
import subprocess
import sys

def ensure_package(package_name, import_name=None):
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"Installing missing package: {package_name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

ensure_package("websockets")
# --- END AUTO INSTALL --- 