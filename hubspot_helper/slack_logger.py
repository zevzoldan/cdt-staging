import os
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

def log_hubspot_update(operation: str, status_code: int, result: dict, error: str = None, thread_ts: str = None):
    """
    Logs HubSpot operation results to Slack in a thread
    
    Args:
        operation: Description of the operation (e.g., "Create Deal", "Update Deal")
        status_code: HTTP status code from HubSpot response
        result: Response data from HubSpot
        error: Error message if any
        thread_ts: Thread timestamp to reply to. If None, starts a new thread
    
    Returns:
        str: The timestamp of the message, useful for threading subsequent messages
    """
    channel = "C08P4TFAPMZ"  # Logging channel ID
    
    # Format the message
    message = f"*HubSpot {operation}*\n"
    message += f"Status Code: {status_code}\n"
    
    if error:
        message += f"❌ Error: {error}\n"
    else:
        message += "✅ Success\n"
    
    # Add result details
    message += f"```{result}```"
    
    # Add deal ID if available for easy reference
    if isinstance(result, dict) and 'id' in result:
        message += f"\nDeal ID: {result['id']}"
    
    try:
        # If no thread_ts provided, this will create a new message
        # If thread_ts is provided, this will reply in the thread
        response = slack_client.chat_postMessage(
            channel=channel,
            text=message,
            mrkdwn=True,
            thread_ts=thread_ts
        )
        return response['ts']  # Return timestamp for threading subsequent messages
    except Exception as e:
        print(f"Error sending log to Slack: {e}")
        return None