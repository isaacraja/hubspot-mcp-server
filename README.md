# HubSpot MCP Server

A simple MCP server for interacting with the HubSpot API, specifically focused on contacts functionality.

## Features

- Get contacts by ID (supports both string and integer format)
- Get contacts by email
- Get deals by ID
- Get contact deals
- Get deal contacts
- Contact engagement analytics
- Search contacts
- Contact schema information
- Deal schema information

## Setup

1. Clone this repository
2. Install dependencies:

```bash
uv pip install -e .
```

3. Set your HubSpot API key as an environment variable:

```bash
export HUBSPOT_API_KEY=your_hubspot_api_key
```

## Usage

### Running with the MCP CLI

You can run the server using the MCP CLI:

```bash
mcp dev server.py
```

### Running directly

Alternatively, you can run it directly:

```bash
python main.py
```

### Installing with Claude Desktop

To install the server with Claude Desktop:

```bash
mcp install server.py
```

### MCP Client Configuration

Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "hubspot": {
      "command": "uv",
      "env": {
        "HUBSPOT_API_KEY": "your_hubspot_api_key"
      },
      "args": [
        "--directory",
        "hubspot-mcp-server",
        "run",
        "server.py"
      ]
    }
  }
}
```

## HubSpot API Key

You'll need a HubSpot API key to use this server. You can get one by:

1. Creating a HubSpot Developer account
2. Creating a private app with contacts permissions
3. Using the generated API key

## Tools

### Contact Tools
- `get_contact_by_id`: Retrieve a contact by their HubSpot ID. Accepts both string IDs (e.g., "108921304388") and integer IDs, with automatic type conversion.
- `get_contact_by_email`: Find a contact by their email address
- `search_contacts`: Search for contacts based on property criteria

### Deal Tools
- `get_deal_by_id`: Retrieve a deal by its HubSpot ID
- `get_contact_deals`: Get all deals associated with a contact
- `get_deal_contacts`: Get all contacts associated with a deal

### Contact Engagement Tools
- `get_latest_marketing_campaign`: Get information about recent marketing campaigns
- `get_campaign_engagement`: Get contacts who engaged with a specific campaign
- `get_page_visits`: Get contacts who visited a specific page
- `get_contact_analytics`: Get analytics data for a specific contact
- `get_scheduled_meetings`: Get meetings scheduled within a time period
- `get_meeting_details`: Get detailed information about a specific meeting

All tools return structured error responses with an `error` field instead of raising exceptions when issues occur, making them more robust for integration.

## Resources

- `hubspot://contacts/schema`: Information about the contact object structure
- `hubspot://deals/schema`: Information about the deal object structure

## Testing

The server includes a comprehensive test suite to ensure functionality works correctly.

### Installing Test Dependencies

```bash
uv pip install -e ".[test]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_hubspot_contacts.py

# Run with coverage
pytest --cov=server
```

The test suite covers:
- Contact lookup functionality by ID and email
- Deal lookup and management functionality
- Contact engagement analytics
- Error handling for API responses
- MCP server configuration
- API communication with HubSpot
- Type handling for IDs (both string and integer formats)

## Code Quality

This project uses [Ruff](https://docs.astral.sh/ruff/) for code formatting and linting.

### Installing Development Dependencies

```bash
uv pip install -e ".[dev]"
```

### Running Linting and Formatting

You can use the provided script to run all formatting and linting in one step:

```bash
./lint.sh
```

Or run the commands individually:

```bash
# Format code
ruff format .

# Check code
ruff check .

# Apply automatic fixes
ruff check --fix .
```

The Ruff configuration is defined in `pyproject.toml` and enforces:
- PEP 8 style guidelines
- Import sorting
- Type annotations
- Code complexity checks
- And more
