"""Simple web server for HazardStack frontend."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn

app = FastAPI(title="HazardStack Web Interface")

# Get the web directory
web_dir = Path(__file__).parent

# Mount static files
app.mount("/static", StaticFiles(directory=web_dir / "static"), name="static")

@app.get("/")
async def root():
    """Serve the main page."""
    return FileResponse(web_dir / "templates" / "index.html")

if __name__ == "__main__":
    print("🌍 Starting HazardStack Web Interface...")
    print("📍 Web UI: http://localhost:3000")
    print("📍 API: http://localhost:8000")
    print("📍 API Docs: http://localhost:8000/docs")
    print("\nMake sure the API is running: docker-compose up -d")

    uvicorn.run(app, host="0.0.0.0", port=3000)
