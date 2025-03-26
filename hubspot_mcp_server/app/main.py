"""
HubSpot MCP Server - Contacts Module

This server provides MCP tools for interacting with HubSpot contacts.
"""

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("HubSpot Contacts")

# Base URL for HubSpot API
HUBSPOT_API_BASE = "https://api.hubapi.com"


# Helper function to get the API key
def get_api_key() -> str:
    """Get the HubSpot API key from environment variables"""
    api_key = os.environ.get("HUBSPOT_API_KEY")
    if not api_key:
        raise ValueError("HUBSPOT_API_KEY environment variable is not set")
    return api_key


# Helper function to create authorized headers
def get_headers() -> dict[str, str]:
    """Create headers with authorization for HubSpot API requests"""
    return {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }


@mcp.tool()
async def get_contact_by_id(contact_id: str | int) -> dict[str, Any]:
    """
    Get a HubSpot contact by ID

    Args:
        contact_id: The HubSpot contact ID (can be string or integer)

    Returns:
        The contact information as a dictionary
    """
    # Convert contact_id to string if it's an integer
    contact_id_str = str(contact_id)

    try:
        async with httpx.AsyncClient() as client:
            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id_str}"
            response = await client.get(url, headers=get_headers())

            if response.status_code == 404:
                return {"error": f"Contact with ID {contact_id_str} not found"}

            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching contact: {error_message}"}

            return response.json()
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.tool()
async def get_contact_by_email(email: str) -> dict[str, Any] | str:
    """
    Get a HubSpot contact by email address

    Args:
        email: The contact's email address

    Returns:
        The contact information as a dictionary or an error message
    """
    try:
        async with httpx.AsyncClient() as client:
            # First, search for contacts with the provided email
            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search"
            search_payload = {
                "filterGroups": [
                    {"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]},
                ],
            }

            response = await client.post(url, headers=get_headers(), json=search_payload)

            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error searching for contact: {error_message}"}

            results = response.json()
            contacts = results.get("results", [])

            if not contacts:
                return {"message": f"No contact found with email: {email}"}

            # Return the first matching contact
            return contacts[0]
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.resource("hubspot://contacts/schema")
def get_contact_schema() -> str:
    """
    Get the schema information for HubSpot contacts

    Returns:
        Information about the contact object structure
    """
    return """
    HubSpot Contact Properties:
    
    - id: The unique identifier for the contact
    - email: The contact's email address
    - firstname: The contact's first name
    - lastname: The contact's last name
    - phone: The contact's phone number
    - company: The contact's company name
    - jobtitle: The contact's job title
    - website: The contact's website
    - address: The contact's address
    - city: The contact's city
    - state: The contact's state
    - zip: The contact's zip code
    - country: The contact's country
    """


if __name__ == "__main__":
    mcp.run()
