# HubSpot MCP Server

A Model Context Protocol server that provides access to the HubSpot API. This server enables LLMs to interact with HubSpot contacts, deals, and engagement data.

## Components

### Tools

The server implements several tools organized by category:

#### Contact Tools
- `get_contact_by_id`: Retrieve a contact by their HubSpot ID (supports both string and integer IDs)
- `get_contact_by_email`: Find a contact by their email address
- `search_contacts`: Search for contacts based on property criteria

#### Deal Tools
- `get_deal_by_id`: Retrieve a deal by its HubSpot ID
- `get_contact_deals`: Get all deals associated with a contact
- `get_deal_contacts`: Get all contacts associated with a deal

#### Engagement Tools
- `get_latest_marketing_campaign`: Get information about recent marketing campaigns
- `get_campaign_engagement`: Get contacts who engaged with a specific campaign
- `get_page_visits`: Get contacts who visited a specific page
- `get_contact_analytics`: Get analytics data for a specific contact
- `get_scheduled_meetings`: Get meetings scheduled within a time period
- `get_meeting_details`: Get detailed information about a specific meeting

### Resources

- `hubspot://contacts/schema`: Information about the contact object structure
- `hubspot://deals/schema`: Information about the deal object structure

## Configuration

The server requires the following configuration:

- `HUBSPOT_API_KEY` (required): Your HubSpot API key from a private app with appropriate permissions

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

##### Development Configuration

```json
"mcpServers": {
  "hubspot": {
    "command": "uv",
    "env": {
      "HUBSPOT_API_KEY": "your_hubspot_api_key"
    },
    "args": [
      "--directory",
      "{{PATH_TO_REPO}}",
      "run",
      "hubspot-mcp-server"
    ]
  }
}
```

Replace `{{PATH_TO_REPO}}` with the path to your cloned repository and `your_hubspot_api_key` with your actual HubSpot API key.

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:

```bash
uv sync
```

2. Build package distributions:

```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:

```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:

- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Testing

Install test dependencies:

```bash
uv sync --extra test
```

Run tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=server
```

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory {{PATH_TO_REPO}} run hubspot-mcp-server
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

## Technical Details

### HubSpot API Integration

- **API Version**: v3
- **Endpoints**: 
  - Contacts: `/crm/v3/objects/contacts`
  - Deals: `/crm/v3/objects/deals`
  - Marketing: `/marketing/v3/campaigns`
  - Analytics: `/analytics/v2`
  - Meetings: `/meetings/v1`
- **Authentication**: API Key in Bearer token

### Getting a HubSpot API Key

You'll need a HubSpot API key to use this server. To get one:

1. Create a HubSpot Developer account
2. Create a private app with required permissions
3. Use the generated API key
