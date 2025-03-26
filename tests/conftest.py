"""
Shared pytest fixtures for testing the HubSpot MCP server
"""

import json
import os
from typing import Any, Dict, List

import pytest


# Sample test data
@pytest.fixture
def sample_contact() -> Dict[str, Any]:
    """Return a sample contact data structure"""
    return {
        "id": "12345",
        "properties": {
            "createdate": "2022-01-01T12:00:00Z",
            "email": "test@example.com",
            "firstname": "Test",
            "hs_object_id": "12345",
            "lastmodifieddate": "2022-01-02T12:00:00Z",
            "lastname": "User",
        },
        "createdAt": "2022-01-01T12:00:00Z",
        "updatedAt": "2022-01-02T12:00:00Z",
        "archived": False,
    }


@pytest.fixture
def sample_contacts_list(sample_contact) -> List[Dict[str, Any]]:
    """Return a list of sample contacts"""
    return {
        "results": [
            sample_contact,
            {
                "id": "67890",
                "properties": {
                    "createdate": "2022-02-01T12:00:00Z",
                    "email": "another@example.com",
                    "firstname": "Another",
                    "hs_object_id": "67890",
                    "lastmodifieddate": "2022-02-02T12:00:00Z",
                    "lastname": "Person",
                },
                "createdAt": "2022-02-01T12:00:00Z",
                "updatedAt": "2022-02-02T12:00:00Z",
                "archived": False,
            },
        ],
        "total": 2,
    }


# Mock response class for API tests
class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data
        self.content = json.dumps(json_data).encode("utf-8")

    def json(self) -> Dict[str, Any]:
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"Status code {self.status_code}")


@pytest.fixture
def mock_response():
    """Factory for creating mock responses with different status codes and data"""

    def _make_mock_response(status_code, json_data) -> MockResponse:
        return MockResponse(status_code, json_data)

    return _make_mock_response


# Mock for httpx.AsyncClient.get
@pytest.fixture
def mock_async_get(mocker):
    """Mock for httpx.AsyncClient.get method"""
    return mocker.patch(
        "httpx.AsyncClient.get",
        return_value=MockResponse(200, {"message": "mock response"}),
    )


# Mock for httpx.AsyncClient.post
@pytest.fixture
def mock_async_post(mocker):
    """Mock for httpx.AsyncClient.post method"""
    return mocker.patch(
        "httpx.AsyncClient.post",
        return_value=MockResponse(200, {"message": "mock response"}),
    )


# Environment setup
@pytest.fixture(autouse=True)
def setup_environment(monkeypatch):
    """Set up environment variables for tests"""
    # Save original environment
    original_env = os.environ.copy()

    # Set test environment
    monkeypatch.setenv("HUBSPOT_API_KEY", "test_api_key_12345")

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
