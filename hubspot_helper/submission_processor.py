import os
from dotenv import load_dotenv
import requests


load_dotenv()
from helpers import slack__get_file_url, slack__get_permalink
from slack_helper import send_deal_review_message


def process_deal_review_submission(datatosend, deal_id):

    print(deal_id, type(deal_id))

    file_urls = datatosend.get("files_for_slack", [])
    slack_send_ts = send_deal_review_message(datatosend)
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
    from hubspot_helper.create_new_record import (
        create_open_community_acquisition_record,
    )

    deal_id = create_open_community_acquisition_record(datatosend, deal_id)

    # save msg to HS
    # get permalink
    if os.environ["ENV"] == "PROD":
        channel_id = "C05HGNS0XR6"
    else:
        channel_id = "C089FAUHSR5"

    permalink = slack__get_permalink(channel_id, slack_send_ts)
    from hubspot_helper.create_new_record import update_deal_stage

    update_deal_stage(deal_id, datatosend={"link_to_slack_post": permalink})


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
