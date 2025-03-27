"""
Tests for HubSpot contacts functionality
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hubspot_mcp_server.server import get_contact_by_email, get_contact_by_id, get_contact_schema

# Sample test data
SAMPLE_CONTACT = {
    "id": "123456789",
    "properties": {
        "email": "test@example.com",
        "firstname": "Test",
        "lastname": "User",
        "phone": "123-456-7890",
        "company": "Test Company",
        "jobtitle": "Test Engineer",
    },
}


class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


# Set up environment variables for tests
@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for tests"""
    os.environ["HUBSPOT_API_KEY"] = "test_api_key"
    yield
    # Clean up after tests
    if "HUBSPOT_API_KEY" in os.environ:
        del os.environ["HUBSPOT_API_KEY"]


# Test get_contact_by_id with a string ID
@pytest.mark.asyncio
async def test_get_contact_by_id_string():
    """Test get_contact_by_id with a string ID"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(200, SAMPLE_CONTACT),
        )

        result = await get_contact_by_id("123456789")

        assert result == SAMPLE_CONTACT
        mock_client.return_value.__aenter__.return_value.get.assert_called_once()


# Test get_contact_by_id with an integer ID
@pytest.mark.asyncio
async def test_get_contact_by_id_integer():
    """Test get_contact_by_id with an integer ID"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(200, SAMPLE_CONTACT),
        )

        # Test with integer ID - this is the key test for validating our fix
        result = await get_contact_by_id(123456789)

        assert result == SAMPLE_CONTACT
        mock_client.return_value.__aenter__.return_value.get.assert_called_once()


# Test get_contact_by_email
@pytest.mark.asyncio
async def test_get_contact_by_email():
    """Test get_contact_by_email function"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_results = {"results": [SAMPLE_CONTACT]}
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=MockResponse(200, mock_results),
        )

        result = await get_contact_by_email("test@example.com")

        assert result == SAMPLE_CONTACT
        mock_client.return_value.__aenter__.return_value.post.assert_called_once()


# Test error handling in get_contact_by_id
@pytest.mark.asyncio
async def test_get_contact_by_id_not_found():
    """Test get_contact_by_id returns appropriate error for 404"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(404, {}),
        )

        result = await get_contact_by_id("not-found")

        assert "error" in result
        assert "not found" in result["error"]


# Test error handling in get_contact_by_email with no results
@pytest.mark.asyncio
async def test_get_contact_by_email_no_results():
    """Test get_contact_by_email with no results"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_results = {"results": []}
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=MockResponse(200, mock_results),
        )

        result = await get_contact_by_email("nonexistent@example.com")

        assert "message" in result
        assert "No contact found" in result["message"]


# Test API error handling
@pytest.mark.asyncio
async def test_api_error_handling():
    """Test error handling for API errors"""
    with patch("httpx.AsyncClient") as mock_client:
        error_response = {"message": "API Error", "status": "error"}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(500, error_response),
        )

        result = await get_contact_by_id("123456789")

        assert "error" in result
        assert "API Error" in result["error"]


# Test get_contact_schema
def test_get_contact_schema():
    """Test get_contact_schema returns valid schema information"""
    schema = get_contact_schema()

    assert isinstance(schema, str)
    assert "HubSpot Contact Properties" in schema
    assert "id:" in schema
    assert "email:" in schema


# Test exception handling
@pytest.mark.asyncio
async def test_exception_handling():
    """Test general exception handling"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Test exception"),
        )

        result = await get_contact_by_id("123456789")

        assert "error" in result
        assert "Test exception" in result["error"]
