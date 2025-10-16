import logging
import os
import re
import json
from typing import Any, Dict, List, Optional, Tuple
import uuid
from box_ai_agents_toolkit import get_ccg_client, box_search


import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class BoxClient:
    """
    Minimal async client for Box API.
    Read-only: you should only pass SELECT / DESCRIBE / SHOW statements.
    """
    

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        subject_type: str,
        subject_id: str,
    ):
        if not client_id:
            raise RuntimeError("client_id is required")
        if not client_secret:
            raise RuntimeError("client_secret is required")
        if not subject_type:
            raise RuntimeError("subject_type is required")
        if not subject_id:
            raise RuntimeError("subject_id is required")

        self.client_id = client_id
        self.client_secret = client_secret
        self.subject_type = subject_type
        self.subject_id = subject_id
        
        self.client = get_ccg_client()
    
    # curl --location 'https://api.box.com/oauth2/token' \
    # --header 'content-type: application/x-www-form-urlencoded' \
    # --header 'Cookie: box_visitor_id=68a22dc3f190b2.92860365; csrf-token=HUBq1Mul1jI0jQM0aUveFWcuF-VcDuwXwhWkijDzM6o' \
    # --data-urlencode 'client_id=a8vi5k6e7380lctol862j916w11kbuuj' \
    # --data-urlencode 'client_secret=dY1ZJ8BEl4FZyQJmKtMoVqfxcdbGzHor' \
    # --data-urlencode 'grant_type=client_credentials' \
    # --data-urlencode 'box_subject_type=user' \
    # --data-urlencode 'box_subject_id=44498056786'

    async def get_access_token(self) -> str:
        """Get a new access token using client credentials grant."""
        url = "https://api.box.com/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "box_subject_type": self.subject_type,
            "box_subject_id": self.subject_id,
        }
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.post(url, headers=headers, data=data)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to get Box access token: {resp.status_code} {resp.text}")
            token_data = resp.json()
            print("Box token data:", token_data)
            access_token = token_data.get("access_token")
            if not access_token:
                raise RuntimeError("No access_token in Box token response")
            print("Obtained Box access token", access_token)
            return access_token

    async def run_box_agents(self, query: str) -> Dict[str, Any]:
        """Run the Cortex agent with the given query, streaming SSE."""
        # Build your payload exactly as before
        results = box_search(self.client, query=query)
        all_raw = [r.to_dict() for r in results]

        print("Search results:", all_raw)

        # all_raw looks like:
        # [{'id': '1957323952488', 'etag': '0', 'type': 'file', 'name': '8176dd22-469c-40b8-8adf-6bfc10ccd9f3_Nova_Control_Panel_-_Feature_Summary.pdf', 'description': '', 'size': 143873}, {'id': '1957326369595', 'etag': '0', 'type': 'file', 'name': 'dab58a51-261d-4368-9049-b5c4b261a136_Release_Notes_Feature_-_Persistent_Storage_Integration.pdf', 'description': '', 'size': 176784}]
        # 
        # Return the content using the following API:
        #
        # curl --location 'https://api.box.com/2.0/files/1957323952488?fields=representations' \
        # --header 'Authorization: Bearer XBJWaoQNOV9JOYIm7hNZGEAzi7tjxuqv' \
        # --header 'x-rep-hints: [extracted_text]'
        # 
        # Its response will contain a URL to download the extracted text content.
        # {
        #     "type": "file",
        #     "id": "1957323952488",
        #     "etag": "0",
        #     "representations": {
        #         "entries": [
        #             {
        #                 "representation": "extracted_text",
        #                 "properties": {},
        #                 "info": {
        #                     "url": "https://api.box.com/2.0/internal_files/1957323952488/versions/2159700786888/representations/extracted_text"
        #                 },
        #                 "status": {
        #                     "state": "success"
        #                 },
        #                 "content": {
        #                     "url_template": "https://dl.boxcloud.com/api/2.0/internal_files/1957323952488/versions/2159700786888/representations/extracted_text/content/{+asset_path}"
        #                 }
        #             }
        #         ]
        #     }
        # }
        #
        # Use the url_template to get the actual content and return as content field.

        for entry in all_raw:
            file_id = entry.get("id")
            if not file_id:
                continue
            url = f"https://api.box.com/2.0/files/{file_id}?fields=representations"
            access_token = await self.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "x-rep-hints": "[extracted_text]"
            }
            async with httpx.AsyncClient() as http_client:
                resp = await http_client.get(url, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"Failed to get representations for file {file_id}: {resp.status_code} {resp.text}")
                    continue
                rep_data = resp.json()
                entries = rep_data.get("representations", {}).get("entries", [])
                for rep in entries:
                    if rep.get("representation") == "extracted_text":
                        content_info = rep.get("content", {})
                        url_template = content_info.get("url_template")
                        if url_template:
                            # Fetch the actual content
                            content_url = url_template.replace("{+asset_path}", "")
                            content_resp = await http_client.get(content_url, headers={"Authorization": f"Bearer {access_token}"})
                            if content_resp.status_code == 200:
                                entry["content"] = content_resp.text
                            else:
                                logger.warning(f"Failed to get extracted text for file {file_id}: {content_resp.status_code} {content_resp.text}")
                        break  # Found the extracted_text representation, no need to check further

        return {
            "results": all_raw
        }

