"""Database connection through sqlalchemy."""

import os

from pydantic import PostgresDsn
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URI = PostgresDsn.build(
    scheme="postgresql",
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    path=f"/{os.environ['DB_NAME']}",
)

# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@postgresserver/db"

engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
