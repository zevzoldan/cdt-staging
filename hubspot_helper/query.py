import requests
import os
from dotenv import load_dotenv

load_dotenv()

CUSTOM_OBJECT_ID = "2-32622392"


def get_all_hubspot_comm_acquisition_records(value):
    print("value", value)
    headers = {
        "Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}",
        "Content-Type": "application/json",
    }
    payload = {
        "properties": ["company_name", "deal_stage", "deal_name___description"],
        "limit": 100,
        "sorts": [{"propertyName": "deal_stage", "direction": "ASCENDING"}],
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "user_id",
                        "operator": "EQ",
                        "value": str(value),
                    },
                ],
            },
        ],
    }

    response = requests.post(
        f"https://api.hubapi.com/crm/v3/objects/2-32622392/search",
        headers=headers,
        json=payload,
    )

    print(f"fetching hubspot records: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        listofrecordsids = []
        listofrecordnames = []
        listofrecorddealstages = []
        listofrecorddescriptions = []
        if results:
            for result in results:
                record_result = result.get("properties", {})
                record_name = record_result.get("company_name", "")
                record_deal_stage = record_result.get("deal_stage", "")
                record_description = record_result.get("deal_name___description", "")
                record_id = result.get("id", "")

                listofrecordsids.append(record_id)
                listofrecordnames.append(record_name)
                listofrecorddealstages.append(record_deal_stage)
                listofrecorddescriptions.append(record_description)
        return list(
            zip(
                listofrecordsids,
                listofrecordnames,
                listofrecorddealstages,
                listofrecorddescriptions,
            )
        )
    else:
        print("error getting hubspot records", response.json())
    return None


def get_hubspot_comm_acquisition_records(value):
    headers = {
        "Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}",
        "Content-Type": "application/json",
    }
    payload = {
        "properties": ["company_name", "deal_stage", "deal_name___description"],
        "limit": 100,
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "user_id",
                        "operator": "EQ",
                        "value": str(value),
                    },
                    {
                        "propertyName": "deal_stage",
                        "operator": "NOT_IN",
                        "values": ["Closed - Lost", "Closed - Won"],
                    },
                ],
            },
        ],
    }

    response = requests.post(
        f"https://api.hubapi.com/crm/v3/objects/2-32622392/search",
        headers=headers,
        json=payload,
    )

    print(f"fetching hubspot records: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        listofrecordsids = []
        listofrecordnames = []
        listofrecorddealstages = []
        listofrecorddescriptions = []
        if results:
            for result in results:
                record_result = result.get("properties", {})
                record_name = record_result.get("company_name", "")
                record_deal_stage = record_result.get("deal_stage", "")
                record_description = record_result.get("deal_name___description", "")
                record_id = result.get("id", "")

                listofrecordsids.append(record_id)
                listofrecordnames.append(record_name)
                listofrecorddealstages.append(record_deal_stage)
                listofrecorddescriptions.append(record_description)
        return list(
            zip(
                listofrecordsids,
                listofrecordnames,
                listofrecorddealstages,
                listofrecorddescriptions,
            )
        )
    else:
        print("error getting hubspot records", response.json())
    return None


def get_contact_id(user_id):
    print(f"finding contact id for user_id: {user_id}")
    headers = {
        "Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}",
        "Content-Type": "application/json",
    }

    # get contact id from email
    payload = {
        "properties": ["email"],
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "community_slack_id",
                        "operator": "EQ",
                        "value": str(user_id),
                    }
                ]
            }
        ],
        "limit": 1,
    }

    response = requests.post(
        f"https://api.hubapi.com/crm/v3/objects/contacts/search",
        headers=headers,
        json=payload,
    )
    print(f"fetching contact id: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        contact_id = data.get("results", [{}])[0].get("id", "")
        return contact_id
    else:
        print("error getting contact id", response.json())
    return None


def deal_data_from_hubspot(deal_id):
    print(f"fetching deal data from hubspot: {deal_id}")

    headers = {
        "Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}",
        "Content-Type": "application/json",
    }

    properties = [
        "company_name",
        "deal_stage",
        "deal_name___description",
        "business_type_industry",
        "deal_purchase_price",
        "location_of_the_business",
        "deal_stage",
        "how_much_of_the_purchase_price_is_for_real_estate_",
        "link_to_your_deal_calculator",
        "sde_calculator_link",
        "deal_box_link",
        "additional_notes__equipment__employees__why_you_like_the_deal_",
        "are_you_providing_sde_or_ebitda_for_earnings___please_specify_which_one_",
        "n2024_sde___ebitda",
        "n2023_sde___ebitda",
        "n2022_sde___ebitda",
        "n2021_sde___ebitda",
        "n2024_revenue",
        "n2023_revenue",
        "n2022_revenue",
        "n2021_revenue",
        "proposed_purchase_price",
        "owner_details__if_any_",
        "are_you_willing_to_share_this_on_mnl_",
        "financing_method",
        "what_are_your_main_concerns_or_questions_",
        "user_id",
        "submitted_by",
        "please_attach_1_3_years_p_l_and_or_taxes__ideally__upload_a_spreadsheet_with_the_p_ls_year_by_year_",
        "company_name",
        "purchase_price",
        "annual_revenue",
        "plans_for_operator",
        "how_did_they_pay_",
        "cash_invested",
        "purchase_agreement",
        "closed_before_or_after_joining_the_community",
        "sba_lender",
        "guidant_used",
        "company_name",
        "where_d_you_find_source_this_deal_",
        "what_is_the_website_",
        "what_is_the_annual_profit",
        "how_many_employees_are_there_",
        "deal_closed",
        "what_are_the_basic_terms_of_the_deal_structure___finances__payment_terms__transition_period__earn_o",
        "how_much_do_you_expect_to_be_able_to_out_in_your_own_pocket_annually__before_growth__with_debt_serv",
        "submitted_by",
        "user_id",
        "we_d_love_to_share_your_success_with_our_audience_on_socials__please_let_us_know_what__if_anything_"
        "if_you_d_like_us_to_tag_you_on_socials__please_list_your_profile_name_s__here_",
        "link_to_slack_post",
        "slack_ts",
    ]

    response = requests.get(
        f"https://api.hubapi.com/crm/v3/objects/2-32622392/{deal_id}",
        headers=headers,
        params={"properties": properties},
    )

    print(f"fetching hubspot deal data: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        return data.get("properties", {})
    else:
        print("error getting deal data", response.json())
    return None
