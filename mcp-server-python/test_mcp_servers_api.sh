#!/bin/bash

# Test script for MCP Servers CRUD API
# Note: Make sure MCP_GATEWAY_URL_POOLS environment variable is set before running this test.
# Example: export MCP_GATEWAY_URL_POOLS="https://mcp1.example.com,https://mcp2.example.com"
BASE_URL="http://localhost:8000/api/v1"

echo "=== Testing MCP Servers CRUD API ==="
echo

# 1. First, sign up a test user
echo "1. Creating test user..."
SIGNUP_RESPONSE=$(curl -s -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "mcpuser@example.com",
    "password": "testpassword123"
  }')
echo "Signup Response: $SIGNUP_RESPONSE"
echo

# 2. Sign in to get token
echo "2. Signing in..."
SIGNIN_RESPONSE=$(curl -s -X POST "$BASE_URL/signin" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "mcpuser@example.com",
    "password": "testpassword123"
  }')
echo "Signin Response: $SIGNIN_RESPONSE"
echo

# 3. Test GET /mcp-servers (should be empty initially)
echo "3. Getting MCP servers (should be empty)..."
SERVERS_LIST=$(curl -s -X GET "$BASE_URL/mcp-servers" \
  -b cookies.txt)
echo "MCP Servers List: $SERVERS_LIST"
echo

# 4. Create a source first (to use in MCP server)
echo "4. Creating a source to use in MCP server..."
SOURCE_RESPONSE=$(curl -s -X POST "$BASE_URL/sources" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "type": "outlook",
    "source_metadata": {
      "tenant_id": "test-tenant-id",
      "graph_client_id": "test-client-id",
      "graph_client_secret": "test-client-secret", 
      "graph_user_id": "test-user-id"
    }
  }')
echo "Created Source: $SOURCE_RESPONSE"

# Extract source ID for use in MCP server
SOURCE_ID=$(echo $SOURCE_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "Extracted Source ID: $SOURCE_ID"
echo

# 5. Create an MCP server without source IDs
echo "5. Creating MCP server (no sources)..."
MCP_SERVER1=$(curl -s -X POST "$BASE_URL/mcp-servers" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Development MCP Server",
    "source_ids": []
  }')
echo "Created MCP Server 1: $MCP_SERVER1"

# Extract server ID for later use
SERVER1_ID=$(echo $MCP_SERVER1 | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "Extracted Server 1 ID: $SERVER1_ID"
echo

# 6. Create another MCP server with source IDs
echo "6. Creating MCP server (with sources)..."
MCP_SERVER2=$(curl -s -X POST "$BASE_URL/mcp-servers" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d "{
    \"name\": \"Production MCP Server\",
    \"source_ids\": [\"$SOURCE_ID\"]
  }")
echo "Created MCP Server 2: $MCP_SERVER2"

# Extract server ID for later use
SERVER2_ID=$(echo $MCP_SERVER2 | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "Extracted Server 2 ID: $SERVER2_ID"
echo

# 7. Create MCP server with invalid source ID (should fail)
echo "7. Testing MCP server creation with invalid source ID..."
INVALID_SERVER=$(curl -s -X POST "$BASE_URL/mcp-servers" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Invalid Server",
    "source_ids": ["invalid-uuid-format"]
  }')
echo "Invalid Server Response: $INVALID_SERVER"
echo

# 8. List all MCP servers
echo "8. Getting all MCP servers..."
ALL_SERVERS=$(curl -s -X GET "$BASE_URL/mcp-servers" \
  -b cookies.txt)
echo "All MCP Servers: $ALL_SERVERS"
echo

# 9. Get specific MCP server by ID
echo "9. Getting MCP server by ID..."
if [ ! -z "$SERVER1_ID" ]; then
  GET_SERVER=$(curl -s -X GET "$BASE_URL/mcp-servers/$SERVER1_ID" \
    -b cookies.txt)
  echo "Get Server Response: $GET_SERVER"
else
  echo "No server ID available for GET request"
fi
echo

# 10. Update MCP server (complete update)
echo "10. Updating MCP server (complete)..."
if [ ! -z "$SERVER1_ID" ]; then
  UPDATE_SERVER=$(curl -s -X PUT "$BASE_URL/mcp-servers/$SERVER1_ID" \
    -H "Content-Type: application/json" \
    -b cookies.txt \
    -d "{
      \"name\": \"Updated Development Server\",
      \"source_ids\": [\"$SOURCE_ID\"]
    }")
  echo "Update Server Response: $UPDATE_SERVER"
else
  echo "No server ID available for UPDATE request"
fi
echo

# 11. Update MCP server (partial - only name)
echo "11. Updating MCP server (partial - name only)..."
if [ ! -z "$SERVER2_ID" ]; then
  PARTIAL_UPDATE=$(curl -s -X PUT "$BASE_URL/mcp-servers/$SERVER2_ID" \
    -H "Content-Type: application/json" \
    -b cookies.txt \
    -d '{
      "name": "Updated Production Server"
    }')
  echo "Partial Update Response: $PARTIAL_UPDATE"
else
  echo "No server ID available for partial UPDATE request"
fi
echo

# 12. Update MCP server with invalid source ID (should fail)
echo "12. Testing update with invalid source ID..."
if [ ! -z "$SERVER1_ID" ]; then
  INVALID_UPDATE=$(curl -s -X PUT "$BASE_URL/mcp-servers/$SERVER1_ID" \
    -H "Content-Type: application/json" \
    -b cookies.txt \
    -d '{
      "source_ids": ["invalid-uuid", "another-invalid-uuid"]
    }')
  echo "Invalid Update Response: $INVALID_UPDATE"
else
  echo "No server ID available for invalid UPDATE request"
fi
echo

# 13. Test GET with invalid server ID
echo "13. Testing GET with invalid server ID..."
INVALID_GET=$(curl -s -X GET "$BASE_URL/mcp-servers/invalid-uuid-format" \
  -b cookies.txt)
echo "Invalid GET Response: $INVALID_GET"
echo

# 14. Test GET with non-existent server ID
echo "14. Testing GET with non-existent server ID..."
NONEXISTENT_GET=$(curl -s -X GET "$BASE_URL/mcp-servers/123e4567-e89b-12d3-a456-426614174000" \
  -b cookies.txt)
echo "Non-existent GET Response: $NONEXISTENT_GET"
echo

# 15. Delete MCP server
echo "15. Deleting MCP server..."
if [ ! -z "$SERVER1_ID" ]; then
  DELETE_SERVER=$(curl -s -X DELETE "$BASE_URL/mcp-servers/$SERVER1_ID" \
    -b cookies.txt)
  echo "Delete Server Response: $DELETE_SERVER"
else
  echo "No server ID available for DELETE request"
fi
echo

# 16. Verify deletion - try to get deleted server
echo "16. Verifying deletion (should return 404)..."
if [ ! -z "$SERVER1_ID" ]; then
  VERIFY_DELETE=$(curl -s -X GET "$BASE_URL/mcp-servers/$SERVER1_ID" \
    -b cookies.txt)
  echo "Verify Delete Response: $VERIFY_DELETE"
else
  echo "No server ID available for verification"
fi
echo

# 17. List servers after deletion
echo "17. Getting all servers after deletion..."
FINAL_LIST=$(curl -s -X GET "$BASE_URL/mcp-servers" \
  -b cookies.txt)
echo "Final Servers List: $FINAL_LIST"
echo

# 18. Delete remaining server
echo "18. Deleting remaining server..."
if [ ! -z "$SERVER2_ID" ]; then
  DELETE_SERVER2=$(curl -s -X DELETE "$BASE_URL/mcp-servers/$SERVER2_ID" \
    -b cookies.txt)
  echo "Delete Server 2 Response: $DELETE_SERVER2"
else
  echo "No server ID available for DELETE request"
fi
echo

# 19. Test unauthorized access (without authentication)
echo "19. Testing unauthorized access..."
UNAUTH_ACCESS=$(curl -s -X GET "$BASE_URL/mcp-servers")
echo "Unauthorized Access Response: $UNAUTH_ACCESS"
echo

# Clean up
rm -f cookies.txt

echo "=== MCP Servers Test Complete ==="
