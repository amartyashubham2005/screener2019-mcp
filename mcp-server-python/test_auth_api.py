#!/usr/bin/env python3
"""
Test script for the MCP Server authentication APIs.
This demonstrates the signup, signin, signout, and me endpoints.

Make sure to:
1. Set up your .env file with DATABASE_URL and JWT_SECRET
2. Run database migrations: alembic upgrade head
3. Start the server: python main.py

Then you can test with:
python test_auth_api.py
"""

import asyncio
import aiohttp
import json
import os

BASE_URL = "http://localhost:8000"

async def test_auth_endpoints():
    """Test all authentication endpoints."""
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Signup
        print("🔐 Testing User Signup...")
        signup_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        async with session.post(f"{BASE_URL}/api/v1/signup", json=signup_data) as resp:
            if resp.status == 200:
                user_data = await resp.json()
                print(f"✅ Signup successful: {user_data['email']} (ID: {user_data['id']})")
            else:
                error = await resp.text()
                print(f"❌ Signup failed: {resp.status} - {error}")
                return
        
        # Test 2: Signin
        print("\n🔑 Testing User Signin...")
        signin_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        access_token = None
        async with session.post(f"{BASE_URL}/api/v1/signin", json=signin_data) as resp:
            if resp.status == 200:
                token_data = await resp.json()
                access_token = token_data["access_token"]
                print(f"✅ Signin successful: Token received")
                print(f"   Cookies: {resp.cookies}")
            else:
                error = await resp.text()
                print(f"❌ Signin failed: {resp.status} - {error}")
                return
        
        # Test 3: Access protected endpoint (/me)
        print("\n👤 Testing Protected Endpoint (/me)...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with session.get(f"{BASE_URL}/api/v1/me", headers=headers) as resp:
            if resp.status == 200:
                user_data = await resp.json()
                print(f"✅ /me endpoint successful: {user_data['email']}")
            else:
                error = await resp.text()
                print(f"❌ /me endpoint failed: {resp.status} - {error}")
        
        # Test 4: Signout
        print("\n🚪 Testing User Signout...")
        async with session.post(f"{BASE_URL}/api/v1/signout") as resp:
            if resp.status == 200:
                response_data = await resp.json()
                print(f"✅ Signout successful: {response_data['message']}")
            else:
                error = await resp.text()
                print(f"❌ Signout failed: {resp.status} - {error}")
        
        # Test 5: Try to access protected endpoint without token
        print("\n🔒 Testing Protected Endpoint without token...")
        async with session.get(f"{BASE_URL}/api/v1/me") as resp:
            if resp.status == 401:
                print("✅ Protected endpoint correctly rejected unauthorized access")
            else:
                print(f"❌ Expected 401, got {resp.status}")

if __name__ == "__main__":
    print("🧪 MCP Server Authentication API Test")
    print("=" * 50)
    print("Make sure the server is running on http://localhost:8000")
    print("=" * 50)
    
    try:
        asyncio.run(test_auth_endpoints())
        print("\n🎉 All tests completed!")
    except aiohttp.ClientConnectorError as e:
        print(f"\n🔌 Connection Error: Could not connect to server at {BASE_URL}")
        print("   Make sure the server is running with: python main.py")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
