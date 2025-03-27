"""
Tests for HubSpot deals functionality
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.append(".")  # Add the root directory to the path
from hubspot_mcp_server.server import get_contact_deals, get_deal_by_id, get_deal_contacts, get_deals_schema

# Sample test data
SAMPLE_DEAL = {
    "id": "987654321",
    "properties": {
        "dealname": "Test Deal",
        "amount": "5000",
        "closedate": "2023-12-31",
        "dealstage": "closedwon",
        "pipeline": "default",
        "dealtype": "newbusiness",
    },
}

SAMPLE_CONTACT = {
    "id": "123456789",
    "properties": {
        "email": "test@example.com",
        "firstname": "Test",
        "lastname": "User",
        "phone": "123-456-7890",
        "company": "Test Company",
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


# Test get_deal_by_id
@pytest.mark.asyncio
async def test_get_deal_by_id():
    """Test get_deal_by_id function"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(200, SAMPLE_DEAL),
        )

        result = await get_deal_by_id("987654321")

        assert result == SAMPLE_DEAL
        mock_client.return_value.__aenter__.return_value.get.assert_called_once()


# Test get_deal_by_id with integer ID
@pytest.mark.asyncio
async def test_get_deal_by_id_integer():
    """Test get_deal_by_id with an integer ID"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(200, SAMPLE_DEAL),
        )

        result = await get_deal_by_id(987654321)

        assert result == SAMPLE_DEAL
        mock_client.return_value.__aenter__.return_value.get.assert_called_once()


# Test get_contact_deals
@pytest.mark.asyncio
async def test_get_contact_deals():
    """Test get_contact_deals function"""
    with patch("httpx.AsyncClient") as mock_client:
        # Mock contact verification
        mock_contact_response = MockResponse(200, SAMPLE_CONTACT)

        # Mock associations response
        mock_associations = {"results": [{"id": "987654321", "type": "deal_to_contact"}]}
        mock_associations_response = MockResponse(200, mock_associations)

        # Mock deal details response
        mock_deal_response = MockResponse(200, SAMPLE_DEAL)

        # Set up the mock client calls sequence
        mock_get = AsyncMock()
        mock_get.side_effect = [
            mock_contact_response,  # First call - contact verification
            mock_associations_response,  # Second call - associations
            mock_deal_response,  # Third call - deal details
        ]
        mock_client.return_value.__aenter__.return_value.get = mock_get

        result = await get_contact_deals("123456789")

        assert result["contact_id"] == "123456789"
        assert result["total_deals"] == 1
        assert len(result["deals"]) == 1
        assert result["deals"][0] == SAMPLE_DEAL
        assert mock_get.call_count == 3


# Test get_deal_contacts
@pytest.mark.asyncio
async def test_get_deal_contacts():
    """Test get_deal_contacts function"""
    with patch("httpx.AsyncClient") as mock_client:
        # Mock deal verification
        mock_deal_response = MockResponse(200, SAMPLE_DEAL)

        # Mock associations response
        mock_associations = {"results": [{"id": "123456789", "type": "contact_to_deal"}]}
        mock_associations_response = MockResponse(200, mock_associations)

        # Mock contact details response
        mock_contact_response = MockResponse(200, SAMPLE_CONTACT)

        # Set up the mock client calls sequence
        mock_get = AsyncMock()
        mock_get.side_effect = [
            mock_deal_response,  # First call - deal verification
            mock_associations_response,  # Second call - associations
            mock_contact_response,  # Third call - contact details
        ]
        mock_client.return_value.__aenter__.return_value.get = mock_get

        result = await get_deal_contacts("987654321")

        assert result["deal_id"] == "987654321"
        assert result["total_contacts"] == 1
        assert len(result["contacts"]) == 1
        assert result["contacts"][0] == SAMPLE_CONTACT
        assert mock_get.call_count == 3


# Test error handling in get_deal_by_id
@pytest.mark.asyncio
async def test_get_deal_by_id_not_found():
    """Test get_deal_by_id returns appropriate error for 404"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(404, {}),
        )

        result = await get_deal_by_id("not-found")

        assert "error" in result
        assert "not found" in result["error"]


# Test get_deals_schema
def test_get_deals_schema():
    """Test get_deals_schema returns valid schema information"""
    schema = get_deals_schema()

    assert isinstance(schema, str)
    assert "HubSpot Deal Properties" in schema
    assert "id:" in schema
    assert "dealname:" in schema
    assert "amount:" in schema
    assert "dealstage:" in schema
