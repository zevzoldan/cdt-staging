import os
from datetime import datetime
from dotenv import load_dotenv
import requests

from hubspot_helper.query import deal_data_from_hubspot


load_dotenv()
from helpers import slack__get_file_url, slack__get_permalink
from slack_helper import send_deal_review_message


def process_deal_review_submission(datatosend, deal_id):

    # if there is a deal id, lets call hubspot and get the existing slack msg. then well update tht msg

    if deal_id:
        deal_data = deal_data_from_hubspot(deal_id)
        slack_send_ts = deal_data.get("slack_ts")
    else:
        slack_send_ts = None

    file_urls = datatosend.get("files_for_slack", [])
    slack_send_ts = send_deal_review_message(datatosend, slack_send_ts)
    clean_file_urls = []
    if os.environ["ENV"] == "PROD":
        channel_id = "C05HGNS0XR6"
    else:
        channel_id = "C089FAUHSR5"

    for file in file_urls:
        file_url = slack__get_file_url(
            file, channel_id=channel_id, slack_ts=slack_send_ts
        )
        clean_file_urls.append(file_url)

    datatosend["file_url"] = ";".join(clean_file_urls)
    datatosend["slack_ts"] = slack_send_ts
    from hubspot_helper.create_new_record import (
        create_open_community_acquisition_record,
    )

    # Get the thread timestamp from the initial Slack message
    thread_ts = helper__send_submission_data_to_slack(
        datatosend.get("user_id"), "deal_review_form", datatosend
    )
    
    # Add thread_ts to datatosend so it can be used for HubSpot operation logging
    datatosend["slack_thread_ts"] = thread_ts
    
    deal_id = create_open_community_acquisition_record(datatosend, deal_id)

    # save msg to HS
    # get permalink
    if os.environ["ENV"] == "PROD":
        channel_id = "C05HGNS0XR6"
    else:
        channel_id = "C089FAUHSR5"

    permalink = slack__get_permalink(channel_id, slack_send_ts)
    from hubspot_helper.create_new_record import update_deal_stage

    update_deal_stage(
        deal_id,
        datatosend={
            "link_to_slack_post": permalink,
            "slack_ts": slack_send_ts,
        },
    )


def helper__send_error_data(error, payload, deal_id):
    print(f"Error: {error}")
    print(f"Payload: {payload}")
    print(f"Deal ID: {deal_id}")

    # make a post request to the error endpoint

    response = requests.post(
        "https://hooks.zapier.com/hooks/catch/10763358/2xf43am/",
        json={"error": error, "payload": payload, "deal_id": deal_id},
    )
    print(response.json())


def helper__send_submission_data_to_slack(user_id, typeofsubmission, datatosend):
    import os
    from slack_sdk import WebClient
    from dotenv import load_dotenv

    load_dotenv()

    slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

    # Create a more descriptive initial message
    msg = slack_client.chat_postMessage(
        channel="C08P4TFAPMZ",
        text=f"New {typeofsubmission} submission from <@{user_id}>",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*New Submission*\nUser: <@{user_id}>\nType: {typeofsubmission}\nTime: <!date^{int(datetime.now().timestamp())}^{'{date_num} {time_secs}'}|now>",
                },
            },
        ],
    )

    msg_ts = msg["ts"]

    # Post submission data in thread
    slack_client.chat_postMessage(
        channel="C08P4TFAPMZ",
        text=f"*Submission Data*\n```{datatosend}```",
        thread_ts=msg_ts,
    )
    
    return msg_ts  # Return the thread timestamp for HubSpot operation logging