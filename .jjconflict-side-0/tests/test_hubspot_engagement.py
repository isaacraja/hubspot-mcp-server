"""
Unit tests for HubSpot contact engagement functions in the MCP server
"""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.append(".")  # Add the root directory to the path
from hubspot_mcp_server.server import (
    get_campaign_engagement,
    get_contact_analytics,
    get_latest_marketing_campaign,
    get_meeting_details,
    get_page_visits,
    get_scheduled_meetings,
    search_contacts,
)

# Sample test data
SAMPLE_CAMPAIGN = {
    "id": "123456",
    "name": "Spring Promotion",
    "type": "EMAIL",
    "subject": "Spring Offers Inside",
    "status": "SENT",
    "sent_date": "2023-03-15T10:00:00Z",
    "stats": {"open_rate": 0.28, "click_rate": 0.12},
}

SAMPLE_ENGAGEMENT = {
    "results": [
        {
            "contact_id": "987654",
            "email": "contact@example.com",
            "time": "2023-03-15T14:22:10Z",
            "type": "OPEN",
            "count": 2,
        },
    ],
    "total": 1,
}

SAMPLE_PAGE_VISITS = {
    "results": [
        {
            "contact_id": "987654",
            "contact_name": "John Smith",
            "url": "https://example.com/pricing",
            "timestamp": "2023-03-20T15:30:00Z",
            "session_id": "sess_123456",
        },
    ],
    "total": 1,
}

SAMPLE_CONTACT_ANALYTICS = {
    "contact_id": "987654",
    "metrics": {"page_views": 12, "form_submissions": 2, "email_clicks": 5},
    "timeframe": "last_7_days",
}

SAMPLE_MEETINGS = {
    "results": [
        {
            "id": "meet_123456",
            "title": "Product Demo",
            "start_time": "2023-03-15T10:00:00Z",
            "end_time": "2023-03-15T11:00:00Z",
            "created_by": "user_123",
            "attendees": ["contact_987654"],
        },
    ],
    "total": 1,
}

SAMPLE_MEETING_DETAILS = {
    "id": "meet_123456",
    "title": "Product Demo",
    "description": "Demonstration of new features",
    "start_time": "2023-03-15T10:00:00Z",
    "end_time": "2023-03-15T11:00:00Z",
    "created_by": "user_123",
    "attendees": [{"id": "contact_987654", "email": "contact@example.com", "name": "John Smith"}],
    "notes": "Customer is interested in the premium plan",
}

SAMPLE_CONTACTS_SEARCH = {
    "results": [
        {
            "id": "987654",
            "properties": {
                "email": "contact@example.com",
                "firstname": "John",
                "lastname": "Smith",
                "phone": "123-456-7890",
                "company": "Example Corp",
            },
        },
    ],
    "total": 1,
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


# Test search_contacts
@pytest.mark.asyncio
async def test_search_contacts():
    """Test search_contacts function"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=MockResponse(200, SAMPLE_CONTACTS_SEARCH),
        )

        result = await search_contacts("lastname", "EQ", "Smith", 10)

        assert result == SAMPLE_CONTACTS_SEARCH
        mock_client.return_value.__aenter__.return_value.post.assert_called_once()


# Test get_latest_marketing_campaign
@pytest.mark.asyncio
async def test_get_latest_marketing_campaign():
    """Test get_latest_marketing_campaign function"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(200, SAMPLE_CAMPAIGN),
        )

        result = await get_latest_marketing_campaign(1, "EMAIL")

        assert result == SAMPLE_CAMPAIGN
        mock_client.return_value.__aenter__.return_value.get.assert_called_once()


# Test get_campaign_engagement
@pytest.mark.asyncio
async def test_get_campaign_engagement():
    """Test get_campaign_engagement function"""
    with patch("httpx.AsyncClient") as mock_client:
        # Mock responses for sequence of API calls
        mock_campaign_response = MockResponse(200, SAMPLE_CAMPAIGN)
        mock_engagement_response = MockResponse(200, {"stats": {"opens": 15, "clicks": 8}})
        mock_contacts_response = MockResponse(200, SAMPLE_ENGAGEMENT)

        mock_get = AsyncMock()
        mock_get.side_effect = [
            mock_campaign_response,  # First call - campaign details
            mock_engagement_response,  # Second call - engagement stats
            mock_contacts_response,  # Third call - contact details
        ]
        mock_client.return_value.__aenter__.return_value.get = mock_get

        result = await get_campaign_engagement("123456", "OPEN", 10)

        assert result == SAMPLE_ENGAGEMENT
        assert mock_get.call_count == 3


# Test get_page_visits
@pytest.mark.asyncio
async def test_get_page_visits():
    """Test get_page_visits function"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=MockResponse(200, SAMPLE_PAGE_VISITS),
        )

        result = await get_page_visits("/pricing", 7, 10)

        assert result == SAMPLE_PAGE_VISITS
        mock_client.return_value.__aenter__.return_value.post.assert_called_once()


# Test get_contact_analytics
@pytest.mark.asyncio
async def test_get_contact_analytics():
    """Test get_contact_analytics function"""
    with patch("httpx.AsyncClient") as mock_client:
        # Mock responses for sequence of API calls
        mock_contact_response = MockResponse(
            200,
            {"id": "987654", "properties": {"email": "contact@example.com"}},
        )
        mock_analytics_response = MockResponse(200, SAMPLE_CONTACT_ANALYTICS)

        mock_get = AsyncMock()
        mock_get.side_effect = [
            mock_contact_response,  # First call - contact verification
            mock_analytics_response,  # Second call - analytics data
        ]
        mock_client.return_value.__aenter__.return_value.get = mock_get

        result = await get_contact_analytics("987654", "page_views", "last_7_days")

        assert result == SAMPLE_CONTACT_ANALYTICS
        assert mock_get.call_count == 2


# Test get_scheduled_meetings
@pytest.mark.asyncio
async def test_get_scheduled_meetings():
    """Test get_scheduled_meetings function"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(200, SAMPLE_MEETINGS),
        )

        # Use specific dates for testing
        result = await get_scheduled_meetings("2023-03-01", "2023-03-31", None, 10)

        assert result == SAMPLE_MEETINGS
        mock_client.return_value.__aenter__.return_value.get.assert_called_once()


# Test get_meeting_details
@pytest.mark.asyncio
async def test_get_meeting_details():
    """Test get_meeting_details function"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(200, SAMPLE_MEETING_DETAILS),
        )

        result = await get_meeting_details("meet_123456")

        assert result == SAMPLE_MEETING_DETAILS
        mock_client.return_value.__aenter__.return_value.get.assert_called_once()


# Test error handling
@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for API errors"""
    with patch("httpx.AsyncClient") as mock_client:
        error_response = {"message": "API Error", "status": "error"}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MockResponse(500, error_response),
        )

        result = await get_latest_marketing_campaign(1, "EMAIL")

        assert "error" in result
        assert "API Error" in result["error"]


# Test required ID validation
@pytest.mark.asyncio
async def test_required_id_validation():
    """Test validation for required IDs"""
    result = await get_meeting_details(None)
    assert "error" in result
    assert "required" in result["error"]
