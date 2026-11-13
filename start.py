"""
BhoomiVaani Full-Stack Runner
Starts both the FastAPI backend and Vite frontend concurrently.
"""
import os
import sys
import subprocess
import time
import signal

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

    # 1. Start Backend
    print("[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=backend_dir,
        env=env,
        shell=(os.name == "nt")
    )

    # Allow backend 1.5 seconds to bind
    time.sleep(1.5)

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
    print("  Press Ctrl+C to terminate both servers.\n")

    def handle_exit(sig, frame):
        print("\n[*] Gracefully stopping BhoomiVaani services...")
        try:
            frontend_proc.terminate()
            backend_proc.terminate()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_exit)

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        handle_exit(None, None)

if __name__ == "__main__":
    main()
