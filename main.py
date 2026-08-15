#!/usr/bin/env python3
"""
FileCustra Application Orchestrator & Launcher
Main entrypoint script to launch frontend (React 19 + Vite) and backend (Python Sidecar & Tauri Core).

Usage:
    python main.py [--dev | --backend-only | --frontend-only | --snapshot-only]
"""

import os
import sys
import subprocess
import time
import signal
import json
import importlib.util

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
SIDECAR_DIR = os.path.join(BACKEND_DIR, "sidecar")
FRONTEND_PUBLIC_DIR = os.path.join(FRONTEND_DIR, "public")
SYSTEM_SNAPSHOT_FILE = os.path.join(FRONTEND_PUBLIC_DIR, "system-snapshot.json")

processes = []

def log(msg, category="INFO"):
    print(f"[{time.strftime('%H:%M:%S')}] [{category}] {msg}")

def check_cmd(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, shell=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def check_environment():
    log("Checking environment dependencies...")
    node_ok = check_cmd(["node", "-v"])
    npm_ok = check_cmd(["npm", "-v"])
    rust_ok = check_cmd(["rustc", "--version"])
    python_version = sys.version.split()[0]
    
    log(f"Python Version: {python_version}")
    log(f"Node.js Available: {node_ok}")
    log(f"npm Available: {npm_ok}")
    log(f"Rustc Available: {rust_ok}")

def generate_system_snapshot():
    sidecar_main = os.path.join(SIDECAR_DIR, "main.py")
    if not os.path.exists(sidecar_main):
        log("Skipping runtime snapshot; sidecar module is missing.", "WARN")
        return

    try:
        spec = importlib.util.spec_from_file_location("filecustra_sidecar", sidecar_main)
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load sidecar module spec.")

        sidecar = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sidecar)
        snapshot = sidecar.system_snapshot({"project_root": PROJECT_ROOT})

        os.makedirs(FRONTEND_PUBLIC_DIR, exist_ok=True)
        with open(SYSTEM_SNAPSHOT_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)

        log(f"Runtime system snapshot written to {SYSTEM_SNAPSHOT_FILE}", "SYSTEM")
    except Exception as exc:
        log(f"Runtime system snapshot unavailable: {exc}", "WARN")

def stream_sidecar_logs(pipe):
    try:
        for line in iter(pipe.readline, ''):
            if line:
                print(f"[BACKEND] {line.strip()}", flush=True)
    except Exception:
        pass

def start_backend_sidecar():
    sidecar_main = os.path.join(SIDECAR_DIR, "main.py")
    if os.path.exists(sidecar_main):
        log("Starting Python Sidecar Backend (JSON-RPC STDIN/STDOUT)...", "BACKEND")
        p = subprocess.Popen(
            [sys.executable, sidecar_main],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=SIDECAR_DIR,
            text=True,
            bufsize=1
        )
        processes.append(p)
        log("Backend Sidecar process spawned successfully.", "BACKEND")

        if p.stderr:
            t = threading.Thread(target=stream_sidecar_logs, args=(p.stderr,), daemon=True)
            t.start()
        return p
    else:
        log(f"Sidecar entrypoint not found at {sidecar_main}", "ERROR")
        return None

def start_frontend_dev_server():
    log("Checking frontend dependencies in frontend/...", "FRONTEND")
    node_modules = os.path.join(FRONTEND_DIR, "node_modules")
    if not os.path.exists(node_modules):
        log("Installing frontend node modules via npm install...", "FRONTEND")
        subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, shell=True)

    log("Starting Vite Frontend Dev Server...", "FRONTEND")
    p = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=True
    )
    processes.append(p)
    log("Frontend Dev Server launching on http://localhost:1420", "FRONTEND")
    return p

def cleanup(signum=None, frame=None):
    log("Shutting down FileCustra background processes...", "SYSTEM")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception:
            p.kill()
    log("All processes terminated cleanly. Exiting.", "SYSTEM")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("=" * 70)
    print("        FileCustra: Agentic File Management System Launcher       ")
    print("=" * 70)

    check_environment()

    # Generate browser-readable local system data before the dashboard loads.
    generate_system_snapshot()

    if "--snapshot-only" in sys.argv:
        log("Snapshot-only mode complete.", "SYSTEM")
        return
    
    # 1. Launch Backend Sidecar
    start_backend_sidecar()

    # 2. Launch Frontend Dev Server
    start_frontend_dev_server()

    log("Application initialized successfully! Press Ctrl+C to terminate all services.", "SYSTEM")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
