"""
HubSpot MCP Server - A Model Context Protocol server for HubSpot API integration
"""

from .server import (
    get_contact_by_id,
    get_contact_by_email,
    search_contacts,
    get_deal_by_id,
    get_contact_deals,
    get_deal_contacts,
    get_latest_marketing_campaign,
    get_campaign_engagement,
    get_page_visits,
    get_contact_analytics,
    get_scheduled_meetings,
    get_meeting_details,
)

__version__ = "0.1.0"

__all__ = [
    "get_contact_by_id",
    "get_contact_by_email",
    "search_contacts",
    "get_deal_by_id",
    "get_contact_deals",
    "get_deal_contacts",
    "get_latest_marketing_campaign",
    "get_campaign_engagement",
    "get_page_visits",
    "get_contact_analytics",
    "get_scheduled_meetings",
    "get_meeting_details",
] 