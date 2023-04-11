"""Placeholder for future Postgres database."""
from pydantic import BaseModel


class Person(BaseModel):
    """Pydantic model for simple test."""

    id: str
    name: str


DB: list[Person] = [
    Person(id=1, name="Sean"),
    Person(id=2, name="Aditya"),
    Person(id=3, name="Nick")
]
