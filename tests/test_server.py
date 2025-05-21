"""
Unit tests for server initialization and configuration
"""

import inspect
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from hubspot_mcp_server import server
from hubspot_mcp_server.server import HUBSPOT_API_BASE

# Instantiate TestClient with the MCP app
client = TestClient(server.mcp.app)


def test_server_has_get_contact_by_id_function():
    """Test that server has the get_contact_by_id function"""
    assert hasattr(server.mcp.tools, "get_contact_by_id")


def test_server_has_get_contact_by_email_function():
    """Test that server has the get_contact_by_email function"""
    assert hasattr(server.mcp.tools, "get_contact_by_email")


def test_server_has_get_contact_schema_function():
    """Test that server has the get_contact_schema function"""
    assert "hubspot://contacts/schema" in server.mcp.resources.keys()


@pytest.mark.asyncio
@patch('hubspot_mcp_server.server.httpx.AsyncClient')
async def test_stream_search_contacts_success_no_pagination(MockAsyncClient):
    """Test successful streaming of contacts (ndjson) without pagination."""
    mock_client_instance = AsyncMock()
    MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

    mock_api_response_data = {
        "results": [
            {"id": "1", "properties": {"email": "test1@example.com", "firstname": "Test"}},
            {"id": "2", "properties": {"email": "test2@example.com", "firstname": "User"}},
        ],
    }

    mock_post_api_response = AsyncMock(spec=httpx.Response)
    mock_post_api_response.status_code = 200
    mock_post_api_response.json.return_value = mock_api_response_data
    mock_post_api_response.raise_for_status = AsyncMock()
    
    mock_client_instance.post.return_value = mock_post_api_response

    payload = {
        "property_name": "email", 
        "operator": "EQ", 
        "value": "test@example.com", 
        "limit": 5
    }
    
    response = client.post("/tools/stream_search_contacts/call", json=payload)
    response.raise_for_status() 

    assert response.headers["content-type"] == "application/x-ndjson" # Reverted to x-ndjson
    
    streamed_items = [json.loads(line) for line in response.iter_lines() if line] # Reverted to iter_lines
    
    assert len(streamed_items) == 2
    expected_contacts = mock_api_response_data["results"]
    assert streamed_items == expected_contacts

    mock_client_instance.post.assert_called_once_with(
        f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search",
        headers=server.get_headers(), 
        json={
            "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": "test@example.com"}]}],
            "limit": 5,
            "properties": ["firstname", "lastname", "email", "phone", "company"],
        },
    )

@pytest.mark.asyncio
@patch('hubspot_mcp_server.server.httpx.AsyncClient')
async def test_stream_search_contacts_success_with_pagination(MockAsyncClient):
    """Test successful streaming (ndjson) with pagination."""
    mock_client_instance = AsyncMock()
    MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

    mock_response_page1_data = {
        "results": [{"id": "1", "properties": {"email": "page1.contact1@example.com", "firstname": "PageOne"}}],
        "paging": {"next": {"link": f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search?after=123"}}
    }
    mock_response_page2_data = {
        "results": [{"id": "2", "properties": {"email": "page2.contact1@example.com", "firstname": "PageTwo"}}]
    }

    mock_post_api_response = AsyncMock(spec=httpx.Response) 
    mock_post_api_response.status_code = 200
    mock_post_api_response.json.return_value = mock_response_page1_data
    mock_post_api_response.raise_for_status = AsyncMock()

    mock_get_api_response = AsyncMock(spec=httpx.Response)
    mock_get_api_response.status_code = 200
    mock_get_api_response.json.return_value = mock_response_page2_data
    mock_get_api_response.raise_for_status = AsyncMock()

    mock_client_instance.post.return_value = mock_post_api_response
    mock_client_instance.get.return_value = mock_get_api_response

    payload = {"property_name": "company", "operator": "EQ", "value": "BigCorp", "limit": 1}
    response = client.post("/tools/stream_search_contacts/call", json=payload)
    response.raise_for_status()

    assert response.headers["content-type"] == "application/x-ndjson" # Reverted
    
    streamed_items = [json.loads(line) for line in response.iter_lines() if line] # Reverted
    
    assert len(streamed_items) == 2
    expected_all_contacts = mock_response_page1_data["results"] + mock_response_page2_data["results"]
    assert streamed_items == expected_all_contacts
    
    mock_client_instance.post.assert_called_once()
    mock_client_instance.get.assert_called_once_with(
        mock_response_page1_data["paging"]["next"]["link"],
        headers=server.get_headers(),
    )

@pytest.mark.asyncio
@patch('hubspot_mcp_server.server.httpx.AsyncClient')
async def test_stream_search_contacts_empty_results(MockAsyncClient):
    """Test streaming empty results (ndjson) using TestClient."""
    mock_client_instance = AsyncMock()
    MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

    mock_api_response_data = {"results": []}
    mock_post_api_response = AsyncMock(spec=httpx.Response)
    mock_post_api_response.status_code = 200
    mock_post_api_response.json.return_value = mock_api_response_data
    mock_post_api_response.raise_for_status = AsyncMock()
    mock_client_instance.post.return_value = mock_post_api_response

    payload = {"property_name": "email", "operator": "EQ", "value": "nonexistent@example.com", "limit": 10}
    response = client.post("/tools/stream_search_contacts/call", json=payload)
    response.raise_for_status()

    assert response.headers["content-type"] == "application/x-ndjson" # Reverted
    
    streamed_items = [json.loads(line) for line in response.iter_lines() if line] # Reverted
    
    assert len(streamed_items) == 1 
    assert streamed_items[0] == {"message": "No contacts found matching criteria."}
    mock_client_instance.post.assert_called_once()

@pytest.mark.asyncio
@patch('hubspot_mcp_server.server.httpx.AsyncClient')
async def test_stream_search_contacts_hubspot_api_error(MockAsyncClient):
    """Test HubSpot API error streaming (ndjson) using TestClient."""
    mock_client_instance = AsyncMock()
    MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

    error_response_body = {"message": "Invalid input", "category": "VALIDATION_ERROR"}
    mock_http_error_response = httpx.Response(
        status_code=400, 
        json=error_response_body,
        request=httpx.Request(method="POST", url=f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search")
    )
    mock_client_instance.post.side_effect = httpx.HTTPStatusError(
        message="Client error", request=mock_http_error_response.request, response=mock_http_error_response
    )
    
    payload = {"property_name": "email", "operator": "EQ", "value": "bad_value", "limit": 10}
    response = client.post("/tools/stream_search_contacts/call", json=payload)
    
    assert response.status_code == 200 
    assert response.headers["content-type"] == "application/x-ndjson" # Reverted

    streamed_items = [json.loads(line) for line in response.iter_lines() if line] # Reverted
    
    assert len(streamed_items) == 1
    assert streamed_items[0] == {
        "error": "HubSpot API Error: 400",
        "details": error_response_body
    }
    mock_client_instance.post.assert_called_once()

@pytest.mark.asyncio
@patch('hubspot_mcp_server.server.httpx.AsyncClient') 
async def test_stream_search_contacts_invalid_operator(MockAsyncClient):
    """Test invalid operator streaming (ndjson) using TestClient."""
    payload = {"property_name": "email", "operator": "INVALID_OP", "value": "test@example.com", "limit": 10}
    response = client.post("/tools/stream_search_contacts/call", json=payload)

    assert response.status_code == 200 
    assert response.headers["content-type"] == "application/x-ndjson" # Reverted

    streamed_items = [json.loads(line) for line in response.iter_lines() if line] # Reverted
        
    assert len(streamed_items) == 1
    operator_mapping_keys = ["EQ", "CONTAINS", "NEQ", "GT", "LT", "GTE", "LTE"]
    expected_error_message = f"Invalid operator. Please use one of: {', '.join(operator_mapping_keys)}"
    assert streamed_items[0] == {"error": expected_error_message}

    MockAsyncClient.return_value.__aenter__.return_value.post.assert_not_called()

@pytest.mark.asyncio
@patch('hubspot_mcp_server.server.httpx.AsyncClient')
async def test_stream_search_contacts_limit_parameter(MockAsyncClient):
    """Test limit parameter handling (ndjson) with TestClient."""
    mock_client_instance = AsyncMock()
    MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

    mock_api_response_data = {"results": []} 
    mock_post_api_response = AsyncMock(spec=httpx.Response)
    mock_post_api_response.status_code = 200
    mock_post_api_response.json.return_value = mock_api_response_data
    mock_post_api_response.raise_for_status = AsyncMock()
    mock_client_instance.post.return_value = mock_post_api_response

    # Test a valid limit
    test_limit = 25
    payload_valid_limit = {"property_name": "firstname", "operator": "CONTAINS", "value": "Alex", "limit": test_limit}
    response_valid = client.post("/tools/stream_search_contacts/call", json=payload_valid_limit)
    response_valid.raise_for_status()
    # Consume response to ensure call is made
    for _ in response_valid.iter_lines(): pass


    mock_client_instance.post.assert_called_with(
        f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search",
        headers=server.get_headers(),
        json={"filterGroups": [{"filters": [{"propertyName": "firstname", "operator": "CONTAINS_TOKEN", "value": "Alex"}]}], "limit": test_limit, "properties": ["firstname", "lastname", "email", "phone", "company"]}
    )

    # Test default limit
    mock_client_instance.post.reset_mock()
    payload_default_limit = {"property_name": "lastname", "operator": "EQ", "value": "Smith"} 
    response_default = client.post("/tools/stream_search_contacts/call", json=payload_default_limit)
    response_default.raise_for_status()
    for _ in response_default.iter_lines(): pass
    
    mock_client_instance.post.assert_called_with(
        f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search",
        headers=server.get_headers(),
        json={"filterGroups": [{"filters": [{"propertyName": "lastname", "operator": "EQ", "value": "Smith"}]}], "limit": 10, "properties": ["firstname", "lastname", "email", "phone", "company"]}
    )

    # Test out-of-bounds limit (e.g., 0)
    mock_client_instance.post.reset_mock()
    payload_low_limit = {"property_name": "lastname", "operator": "EQ", "value": "Doe", "limit": 0}
    response_low = client.post("/tools/stream_search_contacts/call", json=payload_low_limit)
    response_low.raise_for_status()
    for _ in response_low.iter_lines(): pass

    mock_client_instance.post.assert_called_with(
        f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search",
        headers=server.get_headers(),
        json={"filterGroups": [{"filters": [{"propertyName": "lastname", "operator": "EQ", "value": "Doe"}]}], "limit": 10, "properties": ["firstname", "lastname", "email", "phone", "company"]}
    )

    # Test out-of-bounds limit (e.g., 150)
    mock_client_instance.post.reset_mock()
    payload_high_limit = {"property_name": "lastname", "operator": "EQ", "value": "Doe", "limit": 150}
    response_high = client.post("/tools/stream_search_contacts/call", json=payload_high_limit)
    response_high.raise_for_status()
    for _ in response_high.iter_lines(): pass
    
    mock_client_instance.post.assert_called_with(
        f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search",
        headers=server.get_headers(),
        json={"filterGroups": [{"filters": [{"propertyName": "lastname", "operator": "EQ", "value": "Doe"}]}], "limit": 10, "properties": ["firstname", "lastname", "email", "phone", "company"]}
    )
