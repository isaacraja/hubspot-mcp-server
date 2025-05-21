"""
HubSpot MCP Server - Contacts Module

This server provides MCP tools for interacting with HubSpot contacts.
"""

import datetime
import os
from typing import Any, AsyncGenerator 
import json 
import httpx
from mcp.server.fastmcp import FastMCP
# Removed: from starlette.responses import StreamingResponse

# Create the MCP server with stateless_http and json_response enabled
mcp = FastMCP("HubSpot Contacts", stateless_http=True, json_response=True)

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


# Internal implementation
async def _get_contact_by_id(contact_id: str) -> dict[str, Any]:
    """Internal implementation to fetch a contact by ID"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}"
            response = await client.get(url, headers=get_headers())

            if response.status_code == 404:
                return {"error": f"Contact with ID {contact_id} not found"}

            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching contact: {error_message}"}

            return response.json()
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.tool()
async def get_contact_by_id(contact_id=None) -> dict[str, Any]:
    """
    Get a HubSpot contact by ID

    Args:
        contact_id: The HubSpot contact ID. Can be provided as integer or string.

    Returns:
        The contact information as a dictionary
    """
    if contact_id is None:
        return {"error": "Contact ID is required"}
    contact_id_str = str(contact_id)
    return await _get_contact_by_id(contact_id_str)


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
            return contacts[0]
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


# _stream_contact_search_results is removed. Logic merged into stream_search_contacts


@mcp.tool()
async def stream_search_contacts(
    property_name: str, operator: str, value: str, limit: int = 10
) -> AsyncGenerator[dict[str, Any], None]: # Updated signature and return type
    """
    Stream HubSpot contacts based on property criteria.
    Results are yielded as dictionaries.

    Args:
        property_name: The contact property to search (e.g., firstname, lastname, email)
        operator: The operator to use for searching (EQ, CONTAINS, NEQ, GT, LT, GTE, LTE)
        value: The value to search for
        limit: Maximum number of results to return per page (default: 10, max 100 for HubSpot).
               Note: This limit applies to each page fetched from HubSpot.

    Yields:
        Dictionaries representing contacts or error messages.
    """
    # HubSpot's API limit is typically 1 to 100 for search results per page
    if not (1 <= limit <= 100):
        limit = 10 

    operator_mapping = {
        "EQ": "EQ",
        "CONTAINS": "CONTAINS_TOKEN",
        "NEQ": "NEQ",
        "GT": "GT",
        "LT": "LT",
        "GTE": "GTE",
        "LTE": "LTE",
    }

    if operator not in operator_mapping:
        yield {"error": f"Invalid operator. Please use one of: {', '.join(operator_mapping.keys())}"}
        return

    hubspot_operator = operator_mapping[operator]
    search_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search"
    search_payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": property_name,
                        "operator": hubspot_operator,
                        "value": value,
                    },
                ],
            },
        ],
        "limit": limit,
        "properties": ["firstname", "lastname", "email", "phone", "company"], 
    }

    try:
        async with httpx.AsyncClient() as client:
            current_url = search_url
            current_payload = search_payload

            while current_url:
                if current_payload: 
                    response = await client.post(current_url, headers=get_headers(), json=current_payload)
                    current_payload = None 
                else: 
                    response = await client.get(current_url, headers=get_headers())
                
                response.raise_for_status()
                data = response.json()

                contacts = data.get("results", [])
                if not contacts and current_url == search_url and not data.get("paging", {}).get("next", {}).get("link"):
                    yield {"message": "No contacts found matching criteria."}
                    return 

                for contact in contacts:
                    yield contact # Yield dictionary directly
                
                next_link = data.get("paging", {}).get("next", {}).get("link")
                if next_link:
                    current_url = next_link
                else:
                    current_url = None

    except httpx.HTTPStatusError as e:
        error_detail = {}
        try:
            error_detail = e.response.json()
        except json.JSONDecodeError:
            error_detail = {"message": e.response.text or "Unknown HubSpot API error during error parsing"}
        except Exception: 
             error_detail = {"message": "Unknown error during HubSpot error response parsing"}
        yield {"error": f"HubSpot API Error: {e.response.status_code}", "details": error_detail} # Yield dictionary
    except Exception as e:
        yield {"error": f"Server error during streaming: {str(e)}"} # Yield dictionary


@mcp.tool()
async def search_contacts(
    property_name: str,
    operator: str,
    value: str,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Search for HubSpot contacts based on property criteria (non-streaming).

    Args:
        property_name: The contact property to search (e.g., firstname, lastname, email)
        operator: The operator to use for searching (EQ, CONTAINS, NEQ, GT, LT, GTE, LTE)
        value: The value to search for
        limit: Maximum number of results to return (default: 10)

    Returns:
        A dictionary containing matching contacts
    """
    if limit < 1 or limit > 100:
        limit = 10

    operator_mapping = {
        "EQ": "EQ",
        "CONTAINS": "CONTAINS_TOKEN",
        "NEQ": "NEQ",
        "GT": "GT",
        "LT": "LT",
        "GTE": "GTE",
        "LTE": "LTE",
    }

    if operator not in operator_mapping:
        return {
            "error": f"Invalid operator. Please use one of: {', '.join(operator_mapping.keys())}",
        }

    hubspot_operator = operator_mapping[operator]

    try:
        async with httpx.AsyncClient() as client:
            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search"
            search_payload = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": property_name,
                                "operator": hubspot_operator,
                                "value": value,
                            },
                        ],
                    },
                ],
                "limit": limit,
                "properties": ["firstname", "lastname", "email", "phone", "company"],
            }
            response = await client.post(url, headers=get_headers(), json=search_payload)

            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error searching contacts: {error_message}"}

            return response.json()
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.tool()
async def get_deal_by_id(deal_id=None) -> dict[str, Any]:
    """
    Get a HubSpot deal by ID
    Args:
        deal_id: The HubSpot deal ID. Can be provided as integer or string.
    Returns:
        The deal information as a dictionary
    """
    if deal_id is None:
        return {"error": "Deal ID is required"}
    deal_id_str = str(deal_id)
    try:
        async with httpx.AsyncClient() as client:
            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/{deal_id_str}"
            response = await client.get(url, headers=get_headers())
            if response.status_code == 404:
                return {"error": f"Deal with ID {deal_id_str} not found"}
            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching deal: {error_message}"}
            return response.json()
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.tool()
async def get_contact_deals(contact_id=None) -> dict[str, Any]:
    """
    Get all deals associated with a HubSpot contact
    Args:
        contact_id: The HubSpot contact ID. Can be provided as integer or string.
    Returns:
        A dictionary containing the deals associated with the contact
    """
    if contact_id is None:
        return {"error": "Contact ID is required"}
    contact_id_str = str(contact_id)
    try:
        async with httpx.AsyncClient() as client:
            contact_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id_str}"
            contact_response = await client.get(contact_url, headers=get_headers())
            if contact_response.status_code == 404:
                return {"error": f"Contact with ID {contact_id_str} not found"}

            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id_str}/associations/deals"
            response = await client.get(url, headers=get_headers())
            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching contact deals: {error_message}"}
            
            associations = response.json()
            results = associations.get("results", [])
            if not results:
                return {
                    "message": f"No deals found for contact with ID {contact_id_str}",
                    "results": [],
                }

            deals = []
            for association in results:
                deal_id = association.get("id")
                if deal_id:
                    deal_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/{deal_id}?properties=dealname,amount,closedate,dealstage,pipeline"
                    deal_response = await client.get(deal_url, headers=get_headers())
                    if deal_response.status_code == 200:
                        deals.append(deal_response.json())
            return {"contact_id": contact_id_str, "total_deals": len(results), "deals": deals}
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.tool()
async def get_deal_contacts(deal_id=None) -> dict[str, Any]:
    """
    Get all contacts associated with a HubSpot deal
    Args:
        deal_id: The HubSpot deal ID. Can be provided as integer or string.
    Returns:
        A dictionary containing the contacts associated with the deal
    """
    if deal_id is None:
        return {"error": "Deal ID is required"}
    deal_id_str = str(deal_id)
    try:
        async with httpx.AsyncClient() as client:
            deal_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/{deal_id_str}"
            deal_response = await client.get(deal_url, headers=get_headers())
            if deal_response.status_code == 404:
                return {"error": f"Deal with ID {deal_id_str} not found"}

            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/{deal_id_str}/associations/contacts"
            response = await client.get(url, headers=get_headers())
            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching deal contacts: {error_message}"}

            associations = response.json()
            results = associations.get("results", [])
            if not results:
                return {
                    "message": f"No contacts found for deal with ID {deal_id_str}",
                    "results": [],
                }

            contacts = []
            for association in results:
                contact_id = association.get("id")
                if contact_id:
                    contact_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}?properties=firstname,lastname,email,phone,company"
                    contact_response = await client.get(contact_url, headers=get_headers())
                    if contact_response.status_code == 200:
                        contacts.append(contact_response.json())
            
            deal_details = deal_response.json()
            deal_name = deal_details.get("properties", {}).get("dealname", "Unknown Deal")
            return {
                "deal_id": deal_id_str,
                "deal_name": deal_name,
                "total_contacts": len(results),
                "contacts": contacts,
            }
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


# Contact Engagement Tools
@mcp.tool()
async def get_latest_marketing_campaign(limit: int = 1, type: str = "EMAIL") -> dict[str, Any]:
    """
    Get the most recent marketing campaigns
    Args:
        limit: Number of campaigns to retrieve (default: 1)
        type: Campaign type (EMAIL, SOCIAL, etc.)
    Returns:
        Information about the latest marketing campaigns
    """
    try:
        async with httpx.AsyncClient() as client:
            url = f"{HUBSPOT_API_BASE}/marketing/v3/emails"
            params = {"limit": limit, "archived": "false", "sort": "-created"}
            response = await client.get(url, headers=get_headers(), params=params)
            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching marketing campaigns: {error_message}"}
            return response.json()
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.tool()
async def get_campaign_engagement(
    campaign_id=None,
    engagement_type: str = "OPEN",
    limit: int = 10,
) -> dict[str, Any]:
    """
    Get contacts who engaged with a specific marketing campaign
    Args:
        campaign_id: ID of the marketing campaign
        engagement_type: Type of engagement (OPEN, CLICK, etc.)
        limit: Maximum number of contacts to return
    Returns:
        List of contacts with engagement data
    """
    if campaign_id is None:
        return {"error": "Campaign ID is required"}
    campaign_id_str = str(campaign_id)
    try:
        async with httpx.AsyncClient() as client:
            campaign_url = f"{HUBSPOT_API_BASE}/marketing/v3/emails/{campaign_id_str}"
            campaign_response = await client.get(campaign_url, headers=get_headers())
            if campaign_response.status_code == 404:
                return {"error": f"Campaign with ID {campaign_id_str} not found"}
            if campaign_response.status_code != 200:
                error_info = campaign_response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching campaign: {error_message}"}

            engagement_url = f"{HUBSPOT_API_BASE}/marketing/v3/emails/{campaign_id_str}/statistics"
            engagement_response = await client.get(engagement_url, headers=get_headers())
            if engagement_response.status_code != 200:
                error_info = engagement_response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching engagement data: {error_message}"}

            contacts_url = (
                f"{HUBSPOT_API_BASE}/marketing/v3/emails/{campaign_id_str}/statistics/contacts"
            )
            params = {"engagement_type": engagement_type, "limit": limit}
            contacts_response = await client.get(contacts_url, headers=get_headers(), params=params)
            if contacts_response.status_code != 200:
                error_info = contacts_response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching contact engagement data: {error_message}"}
            return contacts_response.json()
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.tool()
async def get_page_visits(
    page_path: str = "/pricing",
    days_ago: int = 7,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Get contacts who visited a specific page in the given time period
    Args:
        page_path: URL path of the page (e.g., "/pricing")
        days_ago: How many days back to look for visits
        limit: Maximum number of contacts to return
    Returns:
        List of contacts with visit data
    """
    try:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).strftime(
            "%Y-%m-%d",
        )
        async with httpx.AsyncClient() as client:
            url = f"{HUBSPOT_API_BASE}/analytics/v3/reports/page-views"
            payload = {
                "timeframe": {"startDate": start_date, "endDate": end_date},
                "filters": [{"operator": "CONTAINS", "property": "path", "value": page_path}],
                "limit": limit,
            }
            response = await client.post(url, headers=get_headers(), json=payload)
            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching page visits: {error_message}"}
            return response.json()
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.tool()
async def get_contact_analytics(
    contact_id=None,
    metrics: str = "page_views",
    timeframe: str = "last_7_days",
) -> dict[str, Any]:
    """
    Get analytics data for a specific contact
    Args:
        contact_id: ID of the contact
        metrics: Types of metrics to retrieve (page_views, form_submissions, etc.)
        timeframe: Time period for data (last_7_days, last_30_days, etc.)
    Returns:
        Analytics data for the contact
    """
    if contact_id is None:
        return {"error": "Contact ID is required"}
    contact_id_str = str(contact_id)
    try:
        async with httpx.AsyncClient() as client:
            contact_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id_str}"
            contact_response = await client.get(contact_url, headers=get_headers())
            if contact_response.status_code == 404:
                return {"error": f"Contact with ID {contact_id_str} not found"}
            if contact_response.status_code != 200:
                error_info = contact_response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching contact: {error_message}"}

            analytics_url = f"{HUBSPOT_API_BASE}/analytics/v3/contacts/{contact_id_str}"
            params = {"metrics": metrics, "timeframe": timeframe}
            analytics_response = await client.get(
                analytics_url,
                headers=get_headers(),
                params=params,
            )
            if analytics_response.status_code != 200:
                error_info = analytics_response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching contact analytics: {error_message}"}
            return analytics_response.json()
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.tool()
async def get_scheduled_meetings(
    start_date: str = None,
    end_date: str = None,
    owner_id: str = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Get meetings scheduled within a time period
    Args:
        start_date: Start of time period (first day of current month by default)
        end_date: End of time period (last day of current month by default)
        owner_id: Optional filter for meetings with a specific owner
        limit: Maximum number of meetings to return
    Returns:
        List of meetings with associated contact information
    """
    if start_date is None:
        today = datetime.datetime.now()
        start_date = datetime.datetime(today.year, today.month, 1).strftime("%Y-%m-%d")
    if end_date is None:
        today = datetime.datetime.now()
        if today.month == 12:
            last_day = datetime.datetime(today.year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            last_day = datetime.datetime(today.year, today.month + 1, 1) - datetime.timedelta(
                days=1,
            )
        end_date = last_day.strftime("%Y-%m-%d")
    try:
        async with httpx.AsyncClient() as client:
            url = f"{HUBSPOT_API_BASE}/meetings/v1/events"
            params = {"startDate": start_date, "endDate": end_date, "limit": limit}
            if owner_id:
                params["ownerId"] = owner_id
            response = await client.get(url, headers=get_headers(), params=params)
            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching scheduled meetings: {error_message}"}
            return response.json()
    except Exception as e:
        return {"error": f"Error processing request: {e!s}"}


@mcp.tool()
async def get_meeting_details(meeting_id=None) -> dict[str, Any]:
    """
    Get detailed information about a specific meeting
    Args:
        meeting_id: ID of the meeting
    Returns:
        Detailed meeting information including attendees, notes, etc.
    """
    if meeting_id is None:
        return {"error": "Meeting ID is required"}
    meeting_id_str = str(meeting_id)
    try:
        async with httpx.AsyncClient() as client:
            url = f"{HUBSPOT_API_BASE}/meetings/v1/events/{meeting_id_str}"
            response = await client.get(url, headers=get_headers())
            if response.status_code == 404:
                return {"error": f"Meeting with ID {meeting_id_str} not found"}
            if response.status_code != 200:
                error_info = response.json()
                error_message = error_info.get("message", "Unknown error")
                return {"error": f"Error fetching meeting details: {error_message}"}
            return response.json()
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


@mcp.resource("hubspot://deals/schema")
def get_deals_schema() -> str:
    """
    Get the schema information for HubSpot deals
    Returns:
        Information about the deal object structure
    """
    return """
    HubSpot Deal Properties:
    
    - id: The unique identifier for the deal
    - dealname: The name of the deal
    - amount: The deal amount
    - closedate: The expected close date
    - dealstage: The stage the deal is in
    - pipeline: The pipeline the deal belongs to
    - dealtype: The type of deal
    - description: Description of the deal
    - createdate: Date the deal was created
    - hs_object_id: The HubSpot object ID (same as id)
    - hs_lastmodifieddate: Date the deal was last modified
    - hubspot_owner_id: The owner of the deal
    """


if __name__ == "__main__":
    mcp.run(transport="streamable-http") # Modified to specify transport
