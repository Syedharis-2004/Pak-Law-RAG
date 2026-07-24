import pytest
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_upload_document_unauthorized(client: AsyncClient):
    response = await client.post("/api/v1/documents/upload")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_upload_document_authorized(client: AsyncClient, admin_token_headers: dict):
    # Mocking file upload
    files = {"file": ("test.txt", b"dummy content", "text/plain")}
    response = await client.post("/api/v1/documents/upload", headers=admin_token_headers, files=files)
    
    # Depending on implementation, might return 202 or 201
    assert response.status_code in [200, 201, 202]
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, admin_token_headers: dict):
    response = await client.get("/api/v1/documents", headers=admin_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)

@pytest.mark.asyncio
async def test_get_document_status(client: AsyncClient, admin_token_headers: dict):
    non_existent = uuid.uuid4()
    response = await client.get(f"/api/v1/documents/{non_existent}/status", headers=admin_token_headers)
    assert response.status_code == 404
