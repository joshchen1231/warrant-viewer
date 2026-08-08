"""Entry point: uvicorn on 127.0.0.1:8000 (PSM §2/§9)."""
import uvicorn

from app import config

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, log_level="info")
