"""
App entry: run the API server. Usage:
  python main.py
  # or: uvicorn api.routes:app --reload --host 0.0.0.0 --port 8000
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.routes:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
