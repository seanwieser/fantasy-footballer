"""Module that contains the backend API."""

from data import DB
from fantasy_footballer.fetcher.fetcher import fetch_members
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    """Root of API."""
    return {"First": "Hello World"}


@app.get("/simpletest")
def read_test():
    """Return example of simple test."""
    return DB


@app.get("/members/{year}")
async def read_page(year: int) -> dict:
    """Path parameter example."""
    return {"members": fetch_members(year)}
