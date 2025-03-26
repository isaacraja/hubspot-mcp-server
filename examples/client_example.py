"""
Example client using mcp_hubspot_get_contact_by_id
"""

import json
import os
import sys

# Add the parent directory to sys.path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import mcp_hubspot_get_contact_by_id


def main() -> None:
    """Example usage of mcp_hubspot_get_contact_by_id"""
    # Replace with a valid contact ID from your HubSpot account
    contact_id = "12345"
    result = mcp_hubspot_get_contact_by_id(contact_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
