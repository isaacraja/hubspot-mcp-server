"""
Tests for HubSpot API communication functionality
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hubspot_mcp_server.server import _get_contact_by_id, get_api_key, get_contact_by_email, get_headers


# Tests for API utility functions
class TestAPIUtils:
    """Tests for API utility functions"""

    def test_get_api_key_success(self):
        """Test successful API key retrieval"""
        with patch.dict(os.environ, {"HUBSPOT_API_KEY": "test_key"}):
            assert get_api_key() == "test_key"

    def test_get_api_key_missing(self):
        """Test API key not found error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as excinfo:
                get_api_key()
            assert "HUBSPOT_API_KEY environment variable is not set" in str(excinfo.value)

    def test_get_headers(self):
        """Test headers construction"""
        with patch("hubspot_mcp_server.server.get_api_key", return_value="test_key"):
            headers = get_headers()
            assert headers["Authorization"] == "Bearer test_key"
            assert headers["Content-Type"] == "application/json"


# Tests for API request construction
class TestAPIRequests:
    """Tests for API request construction"""

    @pytest.mark.asyncio
    async def test_contact_by_id_url_construction(self):
        """Test that the contact by ID URL is correctly constructed"""
        # Mock the response but capture the request URL
        mock_get = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client:
            # Set up the mock to return a success response
            mock_client.return_value.__aenter__.return_value.get = mock_get
            mock_get.return_value.status_code = 200
            mock_get.return_value.json = MagicMock(return_value={})

            # Call the function
            await _get_contact_by_id("12345")

            # Check that the URL was correctly constructed
            called_url = mock_get.call_args[0][0]
            assert called_url == "https://api.hubapi.com/crm/v3/objects/contacts/12345"

    @pytest.mark.asyncio
    async def test_contact_by_email_payload_construction(self):
        """Test that the contact by email search payload is correctly constructed"""
        # Mock the response but capture the request payload
        mock_post = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client:
            # Set up the mock to return a success response
            mock_client.return_value.__aenter__.return_value.post = mock_post
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = MagicMock(return_value={"results": []})

            # Call the function
            await get_contact_by_email("test@example.com")

            # Check that the URL and payload were correctly constructed
            called_url = mock_post.call_args[0][0]
            called_json = mock_post.call_args[1]["json"]

            # Verify URL is correct
            assert called_url == "https://api.hubapi.com/crm/v3/objects/contacts/search"

            # Verify the payload contains the correct email filter
            assert called_json["filterGroups"][0]["filters"][0]["propertyName"] == "email"
            assert called_json["filterGroups"][0]["filters"][0]["operator"] == "EQ"
            assert called_json["filterGroups"][0]["filters"][0]["value"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_api_headers_sent(self):
        """Test that the correct headers are sent with the API request"""
        mock_get = AsyncMock()
        expected_headers = {"Authorization": "Bearer test_key", "Content-Type": "application/json"}

        with (
            patch("httpx.AsyncClient") as mock_client,
            patch("hubspot_mcp_server.server.get_headers", return_value=expected_headers),
        ):
            # Set up the mock to return a success response
            mock_client.return_value.__aenter__.return_value.get = mock_get
            mock_get.return_value.status_code = 200
            mock_get.return_value.json = MagicMock(return_value={})

            # Call the function
            await _get_contact_by_id("12345")

            # Check that the headers were correctly passed
            called_headers = mock_get.call_args[1]["headers"]
            assert called_headers == expected_headers
