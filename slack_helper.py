from datetime import datetime
import os

from slack_sdk import WebClient
from dotenv import load_dotenv


load_dotenv()

slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])


def send_deal_review_message(datatosend, slack_send_ts=None):

    if os.environ["ENV"] == "PROD":
        channel_id = "C05HGNS0XR6"
    else:
        channel_id = "C089FAUHSR5"

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*For Deal Review*"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Name:* <@{datatosend.get('submitted_by')}>",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Are you willing to share this on MNL? {datatosend.get('share_mnl')}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Business Type/Industry:* {datatosend.get('business_type')}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Business Description:* {datatosend.get('business_description')}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Location of the Business:* {datatosend.get('location')}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Basic Numbers:*",
            },
        },
        {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_list",
                    "style": "bullet",
                    "indent": 0,
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"{datatosend.get('earnings_type')}",
                                }
                            ],
                        }
                    ],
                },
                {
                    "type": "rich_text_list",
                    "style": "bullet",
                    "indent": 1,
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"2024: {datatosend.get('sde_ebitda_2024')}",
                                }
                            ],
                        },
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"2023: {datatosend.get('sde_ebitda_2023')}",
                                }
                            ],
                        },
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"2022: {datatosend.get('sde_ebitda_2022')}",
                                }
                            ],
                        },
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"2021: {datatosend.get('sde_ebitda_2021')}",
                                }
                            ],
                        },
                    ],
                },
                {
                    "type": "rich_text_list",
                    "style": "bullet",
                    "indent": 0,
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [{"type": "text", "text": "Revenue"}],
                        }
                    ],
                },
                {
                    "type": "rich_text_list",
                    "style": "bullet",
                    "indent": 1,
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"2024: {datatosend.get('revenue_2024')}",
                                }
                            ],
                        },
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"2023: {datatosend.get('revenue_2023')}",
                                }
                            ],
                        },
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"2022: {datatosend.get('revenue_2022')}",
                                }
                            ],
                        },
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"2021: {datatosend.get('revenue_2021')}",
                                }
                            ],
                        },
                    ],
                },
                {
                    "type": "rich_text_list",
                    "style": "bullet",
                    "indent": 0,
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"Asking Price: {datatosend.get('asking_price')}",
                                }
                            ],
                        },
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"Proposed Purchase Price: {datatosend.get('purchase_price')}",
                                }
                            ],
                        },
                    ],
                },
                {
                    "type": "rich_text_section",
                    "elements": [
                        {
                            "type": "text",
                            "text": "Financing Details",
                        }
                    ],
                },
                {
                    "type": "rich_text_list",
                    "style": "bullet",
                    "indent": 0,
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": f"Share how you intend to finance the deal: {datatosend.get('financing_method')}",
                                }
                            ],
                        }
                    ],
                },
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Deal Stage:* {datatosend.get('deal_stage')}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Owner Details (If Any):*\n{datatosend.get('owner_details')}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*How much of the purchase price is for real estate?:* {datatosend.get('real_estate_percentage')}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Additional Notes:*\n{datatosend.get('additional_notes')}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*What are your main concerns or questions?:*\n{datatosend.get('concerns_questions')}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Here's the link to my Deal Calculator:*\n{datatosend.get('deal_calculator_link')}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Please see the attached 1-3 years P&Ls and/or tax returns below:*",
            },
        },
        # {
        #     "type": "section",
        #     "text": {
        #         "type": "mrkdwn",
        #         "text": "\n ".join(
        #             [f"• {url}" for url in datatosend.get("files_for_slack", [])]
        #         ),
        #     },
        # },
    ]

    if slack_send_ts:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"This deal was updated by <@{datatosend.get('submitted_by')}> on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.",
                    }
                ],
            }
        )
        slack_send = slack_client.chat_update(
            channel=channel_id,
            text="New Deal",
            blocks=blocks,
            ts=slack_send_ts,
        )
    else:
        slack_send = slack_client.chat_postMessage(
            channel=channel_id, text="New Deal", blocks=blocks
        )

    return slack_send.get("ts")


def send_slack_to_success_share_channel(user_id, listofitemstopost):

    if os.environ["ENV"] == "PROD":
        channel_id = "C05GLBYNC06"
    else:
        channel_id = "C089FAUHSR5"
    headerblock = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":rotating_light: *WE'VE GOT A CLOSER!* :rotating_light:\nAnother one of our own - <@{user_id}> - just crossed the finish line and became a business owner.\n\nNo more dreaming. No more “someday.” This member closed the deal and made it real.\n\nLet’s give them a massive shoutout—and if you’ve been lurking, watching from the sidelines, maybe it’s time to step into the arena too.\n\n:point_down: Drop your questions, congrats, and reactions below. Because this isn’t just their win—it’s proof that this stuff works.",
            },
        },
        {
            "type": "divider",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Here's what they want to share with the Community:",
            },
        },
    ]
    blocks = []

    for each_item in listofitemstopost:
        for key, value in each_item.items():
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{key}*: {value}",
                    },
                }
            )
    closeblock = headerblock + blocks
    slack_send = slack_client.chat_postMessage(
        channel=channel_id, text="Success Share", blocks=closeblock
    )

    return slack_send.get("ts")
