import json
import os
from pprint import pprint
from slack_sdk import WebClient
from dotenv import load_dotenv

from hubspot_helper.query import (
    get_all_hubspot_comm_acquisition_records,
    get_hubspot_comm_acquisition_records,
)

load_dotenv()

slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])


def show_app_home_opened(user_id):

    header = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Today's a great day! :sunny:",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Create a New Deal",
                        "emoji": True,
                    },
                    "value": "create_new_deal",
                    "action_id": "create_new_deal",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Update Existing Deal",
                        "emoji": True,
                    },
                    "value": "update_existing_deal",
                    "action_id": "update_existing_deal",
                },
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
    ]
    mydealsblock = []
    records = get_all_hubspot_comm_acquisition_records(user_id)
    if records is None or len(records) == 0:
        mydealsblock = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "No deals found"},
            }
        ]
    else:
        for record in records:
            if record[2] in [
                "Deal Closed",
                "Closed Won",
                "Deal Didn't Close",
                "Closed Lost",
            ]:
                clean_name = f"{record[1]} - {record[3]}"  # max 75 characters
                if len(clean_name) > 70:
                    clean_name = f"{clean_name[:70]}..."
                mydealsblock.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f":tada: *{clean_name}* - {record[2]}",
                        },
                    }
                )
            else:
                clean_name = f"{record[1]} - {record[3]}"  # max 75 characters
                if len(clean_name) > 70:
                    clean_name = f"{clean_name[:70]}..."
                mydealsblock.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{clean_name}* - {record[2]}",
                        },
                        "accessory": {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Update Deal",
                            },
                            "value": f"app_home_update_deal|{record[0]}",
                            "action_id": "update_deal",
                        },
                    }
                )
            mydealsblock.append(
                {
                    "type": "divider",
                }
            )

    blocks = []

    footer = [
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder",
                }
            ],
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "This app was built by <https://linkedin.com/in/zevzoldan|Zev Zoldan>. ",
                },
            ],
        },
    ]

    blocks = header + mydealsblock + footer

    slack_client.views_publish(
        user_id=user_id,
        view={"type": "home", "blocks": blocks},
    )
