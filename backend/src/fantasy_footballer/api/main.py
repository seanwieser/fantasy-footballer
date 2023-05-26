"""Module that contains the backend API."""

# import api.models
# from api.database import engine
from fastapi import FastAPI
from fetcher.fetcher import fetch_members

app = FastAPI()


@app.get("/")
def read_root():
    """Root of API."""
    return {"First": "Hello World"}


@app.get("/members/{year}")
async def read_page(year: int) -> list[str]:
    """Path parameter example."""
    return fetch_members(year)
