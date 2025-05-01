import os
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])


def get_user_name(user_id):
    response = slack_client.users_info(user=user_id)
    return response["user"]


import requests


def slack__get_private_file_url(file):
    file_id = file.get("id")  # Get the correct file ID
    file_name = file.get("name")
    file_size = file.get("size")
    file_url_private = file.get("url_private")

    return file_url_private


def slack__get_file_url(file, channel_id=None, slack_ts=None):
    file_id = file.get("id")  # Get the correct file ID
    file_name = file.get("name")
    file_size = file.get("size")
    file_url_private = file.get("url_private")

    print("Getting file URL for", file_id)

    headers = {"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"}

    try:
        # Step 1: Download the file from Slack
        print("Downloading file from Slack...")
        file_data = requests.get(file_url_private, headers=headers).content
        print("File downloaded successfully")

        # Step 2: Get an upload URL from Slack
        print("Getting upload URL from Slack...")
        response = slack_client.files_getUploadURLExternal(
            filename=file_name,
            length=len(file_data),
        )
        print("Get upload URL external response:", response)

        upload_url = response.get("upload_url")
        new_file_id = response.get("file_id")

        if not upload_url or not new_file_id:
            print("Failed to get upload URL")
            return None

        # Step 3: Upload the file to the provided upload URL
        print("Uploading file to Slack's external upload URL...")
        upload_response = requests.post(upload_url, files={"file": file_data})
        print("Upload response:", upload_response.status_code, upload_response.text)

        if upload_response.status_code != 200:
            print("File upload failed")
            return None

        # Step 4: Complete the external upload
        print("Completing the external upload...")
        complete_response = None
        if channel_id is None:
            complete_response = slack_client.files_completeUploadExternal(
                files=[{"id": new_file_id}],
            )
        else:
            complete_response = slack_client.files_completeUploadExternal(
                channel_id=channel_id,
                thread_ts=slack_ts,
                files=[{"id": new_file_id}],
            )

        # Step 5: Return the external URL
        return complete_response["files"][0]["permalink"]

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def slack__get_permalink(channel_id, slack_ts):

    response = slack_client.chat_getPermalink(channel=channel_id, message_ts=slack_ts)
    return response["permalink"]
