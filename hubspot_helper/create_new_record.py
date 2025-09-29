import requests
import os
import logging
from typing import Optional, Dict, Any
from helpers import get_user_name
from dotenv import load_dotenv
from hubspot_helper.query import get_contact_id
from hubspot_helper.submission_processor import helper__send_error_data
from hubspot_helper.slack_logger import log_hubspot_update

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
CONTACT_OBJECT = "contacts"


def get_headers() -> Dict[str, str]:
    token = os.getenv("HUBSPOT_TOKEN")
    if not token:
        logging.error("HUBSPOT_TOKEN is not set in environment variables.")
        raise EnvironmentError("HUBSPOT_TOKEN is not set.")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def create_closed_community_acquisition_record(
    data: Dict[str, Any], deal_id: Optional[str] = None
) -> Optional[str]:
    # Get thread_ts from data for Slack logging
    thread_ts = data.get("slack_thread_ts")

    headers = get_headers()
    payload = {
        "properties": {
            "deal_stage": f"{data.get('deal_stage')}",
            "purchase_price": f"{data.get('purchase_price', 0)}",
            "annual_revenue": f"{data.get('annual_revenue', 0)}",
            "plans_for_operator": f"{data.get('operator_plan')}",
            "financing_method": f"{data.get('financing_method')}",
            "cash_invested": f"{int(data.get('own_cash', 0))}",
            "purchase_agreement": f"{data.get('file_url')}",
            "closed_before_or_after_joining_the_community": f"{data.get('acquire_deal_before_or_after_joining')}",
            "sba_lender": f"{data.get('sba_loan_lender')}",
            "guidant_used": f"{data.get('guidant_checkbox', 'false')}",
            "company_name": f"{data.get('company_name')}",
            "where_d_you_find_source_this_deal_": f"{data.get('source')}",
            "what_is_the_website_": f"{data.get('website')}",
            "what_is_the_annual_profit": f"{data.get('profit_sde_ebitda', None)}",
            "how_many_employees_are_there_": f"{data.get('employees')}",
            "deal_closed": f"{data.get('date_closed')}",
            "what_are_the_basic_terms_of_the_deal_structure___finances__payment_terms__transition_period__earn_o": f"{data.get('deal_terms')}",
            "how_much_do_you_expect_to_be_able_to_out_in_your_own_pocket_annually__before_growth__with_debt_serv": f"{int(data.get('profit_expectations'))}",
            "submitted_by": f"{get_user_name(data.get('user_id')).get('real_name')}",
            "user_id": f"{data.get('user_id')}",
            "we_d_love_to_share_your_success_with_our_audience_on_socials__please_let_us_know_what__if_anything_": f"{data.get('success_share_checkboxes')}",
            "if_you_d_like_us_to_tag_you_on_socials__please_list_your_profile_name_s__here_": f"{data.get('success_share_text')}",
            "business_type_industry": "Service Businesses - Commercial Laundry / Laundromats and Coin" if data.get('business_type') == "Service Businesses - Commercial Laundry / Laundromats and Coin Laundry" else f"{data.get('business_type')}",
            "location_of_the_business": f"{data.get('location')}",
        }
    }
    url = "https://api.hubapi.com/crm/v3/objects/2-32622392"

    print("handling closed deal in HS")
    slack_thread_ts = data.get("slack_thread_ts")
    if deal_id is None:
        try:
            response = requests.post(
                f"https://api.hubapi.com/crm/v3/objects/2-32622392",
                headers=headers,
                json=payload,
            )
            result = response.json()
            print("creating new deal in HS", result)
            log_hubspot_update("Create Deal", response.status_code, result, thread_ts=thread_ts)
        except Exception as e:
            error_msg = f"Error creating deal: {e}"
            print(error_msg)
            log_hubspot_update("Create Deal", 500, payload, error=error_msg, thread_ts=thread_ts)
            helper__send_error_data(e, payload, deal_id)
            return None

    else:
        print("updating existing deal in HS", deal_id)

        try:
            response = requests.patch(
                f"https://api.hubapi.com/crm/v3/objects/2-32622392/{deal_id}",
                headers=headers,
                json=payload,
            )
            result = response.json()
            print("updating existing deal in HS", deal_id, result)
            thread_ts = log_hubspot_update("Update Deal", response.status_code, result, thread_ts=thread_ts)
        except Exception as e:
            error_msg = f"Error updating deal: {e}"
            print(error_msg)
            log_hubspot_update("Update Deal", 500, payload, error=error_msg, thread_ts=thread_ts)
            helper__send_error_data(e, payload, deal_id)
            return None

    deal_id = response.json().get("id")
    print("deal id is", deal_id)
    if deal_id:
        print("associating deal with contact")
        contact_id = get_contact_id(data.get("user_id"))
        if contact_id is None:
            print("creating new contact record")
            contact_id = create_new_contact_record(data.get("user_id"), thread_ts=thread_ts)
        if contact_id:
            print("associating deal with contact", contact_id)
            associate_deal_with_contact(deal_id, contact_id, thread_ts=thread_ts)

            # TODO Update contact address
            update_contact_address(contact_id, data.get("mailing_address"))


def create_open_community_acquisition_record(
    data: Dict[str, Any], deal_id: Optional[str] = None
) -> Optional[str]:
    # Get thread_ts from data for Slack logging
    thread_ts = data.get("slack_thread_ts")
    headers = get_headers()
    payload = {
        "properties": {
            "company_name": f"{data.get('company_name')}",
            "are_you_willing_to_share_this_on_mnl_": f"{data.get('share_mnl')}",
            "n2025_sde___ebitda": f"{data.get('sde_ebitda_2025')}",
            "n2024_sde___ebitda": f"{data.get('sde_ebitda_2024')}",
            "n2023_sde___ebitda": f"{data.get('sde_ebitda_2023')}",
            "n2022_sde___ebitda": f"{data.get('sde_ebitda_2022')}",
            "n2021_sde___ebitda": f"{data.get('sde_ebitda_2021')}",
            "n2025_revenue": f"{data.get('revenue_2025')}",
            "n2024_revenue": f"{data.get('revenue_2024')}",
            "n2023_revenue": f"{data.get('revenue_2023')}",
            "n2022_revenue": f"{data.get('revenue_2022')}",
            "n2021_revenue": f"{data.get('revenue_2021')}",
            "additional_notes__equipment__employees__why_you_like_the_deal_": f"{data.get('additional_notes')}",
            "are_you_providing_sde_or_ebitda_for_earnings___please_specify_which_one_": f"{data.get('earnings_type').upper()}",
            "deal_purchase_price": f"{int(data.get('asking_price'))}",
            "deal_name___description": f"{data.get('business_description')}",
            "business_type_industry": "Service Businesses - Commercial Laundry / Laundromats and Coin" if data.get('business_type') == "Service Businesses - Commercial Laundry / Laundromats and Coin Laundry" else f"{data.get('business_type')}",
            "deal_stage": f"{data.get('deal_stage')}",
            "how_much_of_the_purchase_price_is_for_real_estate_": f"{data.get('real_estate_percentage')}",
            "link_to_your_deal_calculator": f"{data.get('deal_calculator_link')}",
            "sde_calculator_link": f"{data.get('sde_calculator_link')}",
            "deal_box_link": f"{data.get('deal_box_link')}",
            "location_of_the_business": f"{data.get('location')}",
            "owner_details__if_any_": f"{data.get('owner_details')}",
            "proposed_purchase_price": f"{data.get('purchase_price')}",
            "financing_method": f"{data.get('financing_method')}",
            "what_are_your_main_concerns_or_questions_": f"{data.get('concerns_questions')}",
            "user_id": f"{data.get('user_id')}",
            "submitted_by": f"{get_user_name(data.get('user_id')).get('real_name')}",
            # Only include file data if it's provided (for new deals)
            **({"please_attach_1_3_years_p_l_and_or_taxes__ideally__upload_a_spreadsheet_with_the_p_ls_year_by_year_": data.get("file_url")} if data.get("file_url") else {}),
            "company_name": f"{data.get('company_name', 'New Deal')}",
        }
    }
    try:
        if deal_id is None:
            try:
                response = requests.post(
                    f"https://api.hubapi.com/crm/v3/objects/2-32622392",
                    headers=headers,
                    json=payload,
                )
                result = response.json()
                log_hubspot_update("Create Deal", response.status_code, result, thread_ts=thread_ts)
            except Exception as e:
                error_msg = f"Error creating deal: {e}"
                print(error_msg)
                log_hubspot_update("Create Deal", 500, payload, error=error_msg, thread_ts=thread_ts)
                helper__send_error_data(e, payload, deal_id)
                return None

        else:
            try:
                response = requests.patch(
                    f"https://api.hubapi.com/crm/v3/objects/2-32622392/{deal_id}",
                    headers=headers,
                    json=payload,
                )
                result = response.json()
                log_hubspot_update("Update Deal", response.status_code, result, thread_ts=thread_ts)
            except Exception as e:
                error_msg = f"Error updating deal: {e}"
                print(error_msg)
                log_hubspot_update("Update Deal", 500, payload, error=error_msg, thread_ts=thread_ts)
                helper__send_error_data(e, payload, deal_id)
                return None

    except Exception as e:
        print(f"Error creating open community acquisition record: {e}")
        return None

    try:
        deal_id = response.json().get("id")
        if not deal_id:
            print("No deal ID returned from HubSpot API")
            return None
    except Exception as e:
        print(f"Error getting deal id: {e}")
        return None

    try:
        contact_id = None
        if deal_id:
            contact_id = get_contact_id(data.get("user_id"))
            if contact_id is None:
                contact_id = create_new_contact_record(data.get("user_id"), thread_ts)
            if contact_id:
                associate_deal_with_contact(deal_id, contact_id, thread_ts)
    except Exception as e:
        print(f"Error associating deal with contact: {e}")
        # Continue even if association fails, still return the deal_id

    return deal_id


def associate_deal_with_contact(deal_id: str, contact_id: str, thread_ts: Optional[str] = None):
    headers = get_headers()
    data = '[ { "associationCategory": "USER_DEFINED", "associationTypeId": 81 } ]'
    url = f"https://api.hubapi.com/crm/v4/objects/2-32622392/{deal_id}/associations/contacts/{contact_id}"
    try:
        response = requests.put(url, headers=headers, data=data)
        result = response.json()
        print(result)
        log_hubspot_update("Associate Deal with Contact", response.status_code, result, thread_ts=thread_ts)
    except Exception as e:
        error_msg = f"Error associating deal with contact: {e}"
        print(error_msg)
        log_hubspot_update("Associate Deal with Contact", 500, {"deal_id": deal_id, "contact_id": contact_id}, error=error_msg, thread_ts=thread_ts)
        return None


def create_new_contact_record(user_id: str, thread_ts: Optional[str] = None) -> Optional[str]:
    user_info = get_user_name(user_id)
    first_name = user_info.get("profile").get("first_name")
    last_name = user_info.get("profile").get("last_name")
    email = user_info.get("profile").get("email")

    headers = get_headers()
    payload = {
        "properties": {
            "firstname": f"{first_name}",
            "lastname": f"{last_name}",
            "email": f"{email}",
            "community_slack_id": user_id,
        }
    }
    try:
        url = f"https://api.hubapi.com/crm/v3/objects/contacts"
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        if response.status_code == 200 or response.status_code == 201:
            log_hubspot_update("Create Contact", response.status_code, result, thread_ts=thread_ts)
            contact_id = result.get("id")
            return contact_id
        else:
            log_hubspot_update("Create Contact", response.status_code, result, error="Failed to create contact", thread_ts=thread_ts)
            return None
    except Exception as e:
        error_msg = f"Error creating contact record: {e}"
        print(error_msg)
        log_hubspot_update("Create Contact", 500, payload, error=error_msg, thread_ts=thread_ts)
        return None


def update_contact_address(contact_id: str, address: str):
    headers = get_headers()
    payload = {"properties": {"community_member_mailing_address": f"{address}"}}

    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
    try:
        response = requests.patch(url, headers=headers, json=payload)
        print(response.json())
    except Exception as e:
        print(f"Error updating contact address: {e}")
        return None


def update_deal_stage(deal_id=None, datatosend={}):

    print("updating deal stage", deal_id, datatosend)

    headers = get_headers()
    payload = {"properties": datatosend}

    print("payload", payload)
    try:
        response = None
        if deal_id is None:
            url = f"https://api.hubapi.com/crm/v3/objects/2-32622392"
            response = requests.post(url, headers=headers, json=payload)
        else:
            url = f"https://api.hubapi.com/crm/v3/objects/2-32622392/{deal_id}"

            response = requests.patch(url, headers=headers, json=payload)
        print(response.json())
        return response.json().get("id")
    except Exception as e:
        print(f"Error updating deal stage: {e}")
        return None
