# MCP Servers Management

This directory contains the MCP Servers CRUD functionality for the MCP Admin UI application.

## Overview

The MCP Servers feature allows users to create, read, update, and delete Model Context Protocol (MCP) servers. Each server can be configured with:
- **Name**: A descriptive name for the server
- **Endpoint**: The URL where the MCP server is hosted
- **Sources**: Associated data sources (optional)

## Components

### McpServerForm
A form component for creating and editing MCP servers.

**Props:**
- `initialData?: McpServer | null` - Initial data for editing
- `sources: Source[]` - Available sources to assign
- `sourcesLoading: boolean` - Loading state for sources
- `onSubmit: (data: Omit<McpServer, "id"> | Partial<Omit<McpServer, "id">>) => void` - Submit handler
- `onCancel?: () => void` - Cancel handler for edit mode

### McpServersList  
A list component displaying all MCP servers with their associated sources and actions.

**Props:**
- `mcpServers: McpServer[]` - Array of MCP servers to display
- `sources: Source[]` - Available sources for display mapping
- `loading: boolean` - Loading state
- `onEdit: (server: McpServer) => void` - Edit handler
- `onDelete: (id: string) => void` - Delete handler

## MCP Server Structure

```typescript
interface McpServer {
  id?: string;
  name: string;
  endpoint: string;
  source_ids: string[];
  created_at?: string;
  updated_at?: string;
}
```

## Features

- ✅ Create new MCP servers
- ✅ Assign multiple sources to servers
- ✅ Edit existing servers (complete or partial updates)
- ✅ Delete servers with confirmation
- ✅ Visual source type indicators
- ✅ Source selection with checkboxes
- ✅ Real-time source loading
- ✅ Proper error handling and validation

## API Integration

The MCP Servers feature integrates with the following API endpoints:

- `GET /api/v1/mcp-servers` - Fetch all MCP servers
- `GET /api/v1/mcp-servers/{id}` - Fetch specific MCP server
- `POST /api/v1/mcp-servers` - Create new MCP server
- `PUT /api/v1/mcp-servers/{id}` - Update existing MCP server (supports partial updates)
- `DELETE /api/v1/mcp-servers/{id}` - Delete MCP server

## Usage

Navigate to `/mcp-servers` in the application to access the MCP Servers management interface. The page is divided into two sections:
1. **Left Panel**: Form for creating/editing MCP servers with source selection
2. **Right Panel**: List of existing MCP servers with their associated sources

## Source Assignment

- Sources are displayed with color-coded badges (Outlook=Blue, Snowflake=Purple, Box=Green)
- Multiple sources can be assigned to a single MCP server
- Source assignment is optional
- Sources must be created first before they can be assigned to servers
- Invalid/missing sources are clearly marked in the UI
