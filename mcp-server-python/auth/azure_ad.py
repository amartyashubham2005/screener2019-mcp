import os
import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from authlib.integrations.httpx_client import AsyncOAuth2Client


# Azure AD Configuration
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_REDIRECT_URI = os.getenv("AZURE_REDIRECT_URI")

# Microsoft Graph API endpoints
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
AZURE_AUTHORIZE_URL = f"{AZURE_AUTHORITY}/oauth2/v2.0/authorize"
AZURE_TOKEN_URL = f"{AZURE_AUTHORITY}/oauth2/v2.0/token"
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

# OAuth scopes
AZURE_SCOPES = ["openid", "profile", "email", "User.Read"]


class AzureADService:
    """Service for Azure AD OAuth 2.0 authentication."""

    @staticmethod
    def get_authorization_url(state: str) -> str:
        """
        Generate the Azure AD authorization URL for initiating OAuth flow.

        Args:
            state: CSRF protection state parameter

        Returns:
            Authorization URL to redirect the user to
        """
        if not all([AZURE_CLIENT_ID, AZURE_REDIRECT_URI, AZURE_TENANT_ID]):
            raise ValueError("Azure AD configuration is incomplete. Please set AZURE_CLIENT_ID, AZURE_REDIRECT_URI, and AZURE_TENANT_ID environment variables.")

        params = {
            "client_id": AZURE_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": AZURE_REDIRECT_URI,
            "response_mode": "query",
            "scope": " ".join(AZURE_SCOPES),
            "state": state,
        }

        # Use urlencode to properly encode all parameters
        query_string = urlencode(params)
        return f"{AZURE_AUTHORIZE_URL}?{query_string}"

    @staticmethod
    async def exchange_code_for_token(code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Azure AD callback

        Returns:
            Token response containing access_token, id_token, etc.
        """
        if not all([AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_REDIRECT_URI]):
            raise ValueError("Azure AD configuration is incomplete.")

        client = AsyncOAuth2Client(
            client_id=AZURE_CLIENT_ID,
            client_secret=AZURE_CLIENT_SECRET,
            token_endpoint=AZURE_TOKEN_URL
        )

        try:
            token = await client.fetch_token(
                url=AZURE_TOKEN_URL,
                code=code,
                redirect_uri=AZURE_REDIRECT_URI,
                grant_type="authorization_code"
            )
            return token
        except Exception as e:
            print(f"Error exchanging code for token: {e}")
            return None

    @staticmethod
    async def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Microsoft Graph API.

        Args:
            access_token: Azure AD access token

        Returns:
            User information dictionary containing id, email, name, etc.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{GRAPH_API_ENDPOINT}/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                user_data = response.json()

                return {
                    "azure_id": user_data.get("id"),
                    "email": user_data.get("mail") or user_data.get("userPrincipalName"),
                    "full_name": user_data.get("displayName"),
                    "given_name": user_data.get("givenName"),
                    "surname": user_data.get("surname"),
                }
            except Exception as e:
                print(f"Error fetching user info: {e}")
                return None

    @staticmethod
    def validate_config() -> bool:
        """
        Validate that all required Azure AD configuration is present.

        Returns:
            True if configuration is valid, False otherwise
        """
        return all([
            AZURE_CLIENT_ID,
            AZURE_CLIENT_SECRET,
            AZURE_TENANT_ID,
            AZURE_REDIRECT_URI
        ])
