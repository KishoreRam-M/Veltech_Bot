import pytest
import asyncio
from httpx import AsyncClient
from server.app import app
import os
import numpy as np

# Pytest fixtures and helpers

@pytest.mark.asyncio
async def test_t01_english_happy_path():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/chat", json={"query": "What are the courses offered?"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] in ["course_inquiry", "general"]
    assert "response" in data

@pytest.mark.asyncio
async def test_t02_tamil_unicode():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/chat", json={"query": "கல்லூரியில் என்ன படிப்புகள் உள்ளன?"})
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "ta"

@pytest.mark.asyncio
async def test_t03_tanglish():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/chat", json={"query": "College la enna courses irukku?"})
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "tanglish"

@pytest.mark.asyncio
async def test_t06_empty_input():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/chat", json={"query": ""})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_t07_whitespace_input():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/chat", json={"query": "   "})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_t14_oversized_input():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/chat", json={"query": "A" * 5001})
    assert response.status_code == 422 # Pydantic validation error
