"""
BhoomiVaani Full-Stack Runner
Starts both the FastAPI backend and Vite frontend concurrently.
"""
import os
import sys
import subprocess
import time
import signal
import urllib.error
import urllib.request

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")

    print("=" * 65)
    print("  BHOOMIVAANI | AI Voice-First Land Intelligence Platform")
    print("=" * 65)
    print(f"[*] Root Directory:     {root_dir}")
    print(f"[*] Backend Directory:  {backend_dir}")
    print(f"[*] Frontend Directory: {frontend_dir}")
    print("=" * 65)

    # Set PYTHONPATH
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{backend_dir}{os.pathsep}{current_pythonpath}"

    backend_url = "http://127.0.0.1:8000/api/health"

    def backend_is_ready():
        try:
            with urllib.request.urlopen(backend_url, timeout=1) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    # Reuse an API started separately; otherwise launch it here.
    backend_proc = None
    if backend_is_ready():
        print("[1/2] Reusing FastAPI Backend on http://127.0.0.1:8000")
    else:
        print("[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
        backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
            env=env,
            shell=(os.name == "nt")
        )

    # Do not advertise a working frontend until the API is ready to accept requests.
    backend_ready = False
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if backend_proc is not None and backend_proc.poll() is not None:
            print(f"[!] FastAPI exited during startup (code {backend_proc.returncode}); frontend was not started.")
            return
        if backend_is_ready():
            backend_ready = True
            break
        time.sleep(0.25)

    if not backend_ready:
        print("[!] FastAPI did not become ready within 20 seconds; frontend was not started.")
        if backend_proc is not None:
            backend_proc.terminate()
        return

    # 2. Start Frontend
    print("[2/2] Starting Vite Frontend on http://localhost:5173 ...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev", "--", "--host", "0.0.0.0"],
        cwd=frontend_dir,
        shell=(os.name == "nt")
    )

    print("\n" + "=" * 65)
    print("  SERVICES RUNNING:")
    print("  - Frontend UI:  http://localhost:5173")
    print("  - Backend API:  http://127.0.0.1:8000")
    print("  - Swagger Docs: http://127.0.0.1:8000/docs")
    print("  - Health Check: http://127.0.0.1:8000/api/health")
    print("=" * 65)
    print("  Press Ctrl+C to stop the services started by this runner.\n")

    def handle_exit(sig, frame):
        print("\n[*] Gracefully stopping BhoomiVaani services...")
        if frontend_proc.poll() is None:
            frontend_proc.terminate()
        if backend_proc is not None and backend_proc.poll() is None:
            backend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_exit)

    try:
        while frontend_proc.poll() is None and (
            backend_proc is None or backend_proc.poll() is None
        ):
            time.sleep(0.25)
    except KeyboardInterrupt:
        handle_exit(None, None)
    else:
        handle_exit(None, None)

if __name__ == "__main__":
    main()
