# Sources Management

This directory contains the Sources CRUD functionality for the MCP Admin UI application.

## Overview

The Sources feature allows users to create, read, update, and delete different types of data sources:
- **Outlook**: Microsoft Graph API integration
- **Snowflake**: Snowflake data platform integration
- **Box**: Box cloud storage integration

## Components

### SourceForm
A form component for creating and editing sources with dynamic fields based on the selected source type.

**Props:**
- `initialData?: Source | null` - Initial data for editing
- `onSubmit: (data: Omit<Source, "id">) => void` - Submit handler
- `onCancel?: () => void` - Cancel handler for edit mode

### SourcesList  
A list component displaying all sources with edit and delete actions.

**Props:**
- `sources: Source[]` - Array of sources to display
- `loading: boolean` - Loading state
- `onEdit: (source: Source) => void` - Edit handler
- `onDelete: (id: string) => void` - Delete handler

## Source Types

### Outlook Source
Required fields:
- `tenant_id`: Azure AD tenant ID
- `graph_client_id`: Microsoft Graph client ID  
- `graph_client_secret`: Microsoft Graph client secret
- `graph_user_id`: Target user ID for Graph API

### Snowflake Source
Required fields:
- `snowflake_account_url`: Snowflake account URL
- `snowflake_pat`: Personal Access Token
- `snowflake_semantic_model_file`: Semantic model file path
- `snowflake_cortex_search_service`: Cortex search service name

### Box Source
Required fields:
- `box_client_id`: Box application client ID
- `box_client_secret`: Box application client secret
- `box_subject_type`: Subject type (typically "user")
- `box_subject_id`: Subject ID for Box API authentication

## API Integration

The Sources feature integrates with the following API endpoints:

- `GET /api/v1/sources` - Fetch all sources
- `POST /api/v1/sources` - Create new source
- `PUT /api/v1/sources/{id}` - Update existing source
- `DELETE /api/v1/sources/{id}` - Delete source

## Usage

Navigate to `/sources` in the application to access the Sources management interface. The page is divided into two sections:
1. **Left Panel**: Form for creating/editing sources
2. **Right Panel**: List of existing sources

## Features

- ✅ Dynamic form fields based on source type
- ✅ Real-time validation
- ✅ Edit existing sources
- ✅ Delete sources with confirmation
- ✅ Toast notifications for actions
- ✅ Loading states
- ✅ Responsive design matching app theme
- ✅ Type-safe TypeScript implementation
