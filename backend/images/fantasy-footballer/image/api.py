"""Module that contains the backend API."""

from fantasy_footballer.fetcher.fetcher import fetch_members
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    """Root of API."""
    return {"First": "Hello World"}


@app.get("/members/{year}")
async def read_page(year: int) -> list[str]:
    """Path parameter example."""
    return fetch_members(year)
