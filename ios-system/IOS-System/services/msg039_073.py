"""
Slack integration
"""

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.signature import SignatureVerifier

class SlackIntegration:
    """Slack connector"""
    
    def __init__(self):
        self.client = AsyncWebClient(token=settings.slack_bot_token)
        self.verifier = SignatureVerifier(settings.slack_signing_secret)
    
    async def send_notification(
        self,
        channel: str,
        message: str,
        document_id: Optional[str] = None
    ):
        """Send notification to Slack"""
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
        
        if document_id:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Document"},
                        "url": f"{settings.app_url}/documents/{document_id}"
                    }
                ]
            })
        
        await self.client.chat_postMessage(
            channel=channel,
            blocks=blocks
        )
    
    async def handle_slash_command(self, command: str, text: str) -> Dict:
        """Handle Slack slash commands"""
        
        if command == "/ios-search":
            # Search and return results
            results = await self.search_service.search(text)
            
            return {
                "response_type": "ephemeral",
                "text": f"Found {len(results)} results",
                "attachments": self._format_search_results(results)
            }
        
        elif command == "/ios-upload":
            # Generate upload URL
            upload_url = await self.generate_upload_url()
            
            return {
                "response_type": "ephemeral",
                "text": f"Upload your document here: {upload_url}"
            }