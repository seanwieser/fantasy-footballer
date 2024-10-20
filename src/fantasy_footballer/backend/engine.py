"""Database connection through sqlalchemy."""

import os
import socket
from string import Template

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = Template(
    "${driver}://${username}:${password}@${host}:${port}/${db}")

ASYNC_URI = SQLALCHEMY_DATABASE_URL.substitute(
    driver="postgresql+asyncpg",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port="5432",
    db=os.environ["DB_NAME"])
async_engine = create_async_engine(ASYNC_URI, pool_pre_ping=True)
async_session = async_sessionmaker(bind=async_engine, autoflush=False, autocommit=False, expire_on_commit=False)

URI = SQLALCHEMY_DATABASE_URL.substitute(driver="postgresql",
                                         username=os.environ["DB_USER"],
                                         password=os.environ["DB_PASSWORD"],
                                         host=os.environ["DB_HOST"],
                                         port="5432",
                                         db=os.environ["DB_NAME"])
engine = create_engine(URI, pool_pre_ping=True)
session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
