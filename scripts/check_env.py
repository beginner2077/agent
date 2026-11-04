"""Offline checks for the course environment; no model requests or credentials."""

import sqlite3
import sys
from importlib.metadata import version
from pathlib import Path

import tomllib


def main():
    root = Path(__file__).resolve().parents[1]
    if sys.version_info[:2] != (3, 12) or Path(sys.prefix).resolve() != root / ".venv":
        raise RuntimeError("Run this with .venv/Scripts/python.exe (Python 3.12).")
    print("Python:", sys.version.split()[0])
    project = tomllib.loads((root / "course-assignments/pyproject.toml").read_text("utf-8"))
    dependencies = project["tool"]["poetry"]["dependencies"]
    development = project["tool"]["poetry"]["group"]["dev"]["dependencies"]
    for package in sorted((dependencies.keys() | development.keys()) - {"python"}):
        print(f"{package}: {version(package)}")

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    with TestClient(app) as client:
        response = client.get("/health")
        if response.status_code != 200 or response.json() != {"status": "ok"}:
            raise RuntimeError("FastAPI/HTTPX local request failed.")
    with sqlite3.connect(":memory:") as database:
        if database.execute("SELECT 1").fetchone() != (1,):
            raise RuntimeError("SQLite check failed.")
    print("PASS: course packages, local FastAPI request, SQLite.")
    print("Not tested: external model API, paid usage, real session capture.")


if __name__ == "__main__":
    main()
