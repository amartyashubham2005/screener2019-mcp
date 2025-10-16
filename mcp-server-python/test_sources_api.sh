#!/bin/bash

# Test script for Sources CRUD API
BASE_URL="http://localhost:8000/api/v1"

echo "=== Testing Sources CRUD API ==="
echo

# 1. First, sign up a test user
echo "1. Creating test user..."
SIGNUP_RESPONSE=$(curl -s -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
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
    "email": "testuser@example.com",
    "password": "testpassword123"
  }')
echo "Signin Response: $SIGNIN_RESPONSE"
echo

# 3. Test GET /sources (should be empty initially)
echo "3. Getting sources (should be empty)..."
SOURCES_LIST=$(curl -s -X GET "$BASE_URL/sources" \
  -b cookies.txt)
echo "Sources List: $SOURCES_LIST"
echo

# 4. Create an Outlook source
echo "4. Creating Outlook source..."
OUTLOOK_SOURCE=$(curl -s -X POST "$BASE_URL/sources" \
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
echo "Created Outlook Source: $OUTLOOK_SOURCE"
echo

# 5. Create a Snowflake source
echo "5. Creating Snowflake source..."
SNOWFLAKE_SOURCE=$(curl -s -X POST "$BASE_URL/sources" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "type": "snowflake",
    "source_metadata": {
      "snowflake_account_url": "https://test.snowflakecomputing.com",
      "snowflake_pat": "test-pat-token",
      "snowflake_semantic_model_file": "test-model.yaml",
      "snowflake_cortex_search_service": "test-search-service"
    }
  }')
echo "Created Snowflake Source: $SNOWFLAKE_SOURCE"
echo

# 6. List all sources
echo "6. Getting all sources..."
ALL_SOURCES=$(curl -s -X GET "$BASE_URL/sources" \
  -b cookies.txt)
echo "All Sources: $ALL_SOURCES"
echo

# Clean up
rm -f cookies.txt

echo "=== Test Complete ==="
