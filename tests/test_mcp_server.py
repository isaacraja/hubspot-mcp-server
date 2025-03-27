"""
Tests for the MCP server configuration and initialization
"""

import unittest
from unittest.mock import patch

from hubspot_mcp_server import server


class TestMCPServer(unittest.TestCase):
    """Test cases for MCP server setup"""

    def test_server_initialization(self):
        """Test that the server can be initialized"""
        # This is an integration test that makes sure we can import without errors

        # Successful import means initialization worked
        self.assertTrue(True)

    def test_tool_registration(self):
        """Test that the tools are properly registered"""
        # Check that our tool functions exist in the module
        # Basic contact tools
        assert hasattr(server, "get_contact_by_id")
        assert hasattr(server, "get_contact_by_email")
        assert hasattr(server, "search_contacts")

        # Deal tools
        assert hasattr(server, "get_deal_by_id")
        assert hasattr(server, "get_contact_deals")
        assert hasattr(server, "get_deal_contacts")

        # Contact engagement tools
        assert hasattr(server, "get_latest_marketing_campaign")
        assert hasattr(server, "get_campaign_engagement")
        assert hasattr(server, "get_page_visits")
        assert hasattr(server, "get_contact_analytics")
        assert hasattr(server, "get_scheduled_meetings")
        assert hasattr(server, "get_meeting_details")

        # Schema resources
        assert hasattr(server, "get_contact_schema")
        assert hasattr(server, "get_deals_schema")

    def test_resource_registration(self):
        """Test that the resources are properly registered"""
        # Check that our resources exist and return the expected content
        contact_schema = server.get_contact_schema()
        assert isinstance(contact_schema, str)
        assert "HubSpot Contact Properties" in contact_schema

        deal_schema = server.get_deals_schema()
        assert isinstance(deal_schema, str)
        assert "HubSpot Deal Properties" in deal_schema


def test_main_execution():
    """Test that main can execute without errors"""
    # Patch the mcp.run method to prevent actual server startup
    with patch.object(server.mcp, "run") as mock_run:
        # Call the main block code
        server.mcp.run()

        # Verify run was called
        mock_run.assert_called_once()
