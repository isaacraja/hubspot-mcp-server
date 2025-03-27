"""
Unit tests for server initialization and configuration
"""

import inspect

from hubspot_mcp_server import server


def test_server_has_get_contact_by_id_function():
    """Test that server has the get_contact_by_id function"""
    assert hasattr(server, "get_contact_by_id")
    assert inspect.iscoroutinefunction(server.get_contact_by_id)


def test_server_has_get_contact_by_email_function():
    """Test that server has the get_contact_by_email function"""
    assert hasattr(server, "get_contact_by_email")
    assert inspect.iscoroutinefunction(server.get_contact_by_email)


def test_server_has_get_contact_schema_function():
    """Test that server has the get_contact_schema function"""
    assert hasattr(server, "get_contact_schema")
    assert inspect.isfunction(server.get_contact_schema)
