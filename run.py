"""
IndicRAG-QA Quick Launcher
Start the server with:
    python run.py
    python run.py --port 8080
"""
import sys
import argparse
from pathlib import Path
import uvicorn

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

def main():
    parser = argparse.ArgumentParser(description="Start IndicRAG-QA Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print(" IndicRAG-QA Server Starting")
    print(f" Web UI:       http://localhost:{args.port}/")
    print(f" Swagger Docs: http://localhost:{args.port}/api/docs")
    print("=" * 65 + "\n")

    uvicorn.run("app.api.main:app", host=args.host, port=args.port, app_dir=str(BACKEND_DIR))

if __name__ == "__main__":
    main()
