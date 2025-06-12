import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

from datetime import datetime
import json
import os
from pprint import pprint
from slack_sdk import WebClient
from dotenv import load_dotenv

from hubspot_helper.query import (
    deal_data_from_hubspot,
    get_hubspot_comm_acquisition_records,
)

load_dotenv()

slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])


def deal_stage_list_as_options():
    # Other
    # NDA Signed
    # LOI Signed
    # Purchase Agreement Submitted
    # Offer Made
    # Offer Accepted
    # Offer Not Made
    # Offer Not Accepted
    # LOI Submitted
    # Purchase Agreement Accepted
    # Deal Closed
    # Deal Didn't Close
    return [
        {
            "text": {"type": "plain_text", "text": "NDA Signed"},
            "value": "NDA Signed",
        },
        {
            "text": {"type": "plain_text", "text": "LOI Submitted"},
            "value": "LOI Submitted",
        },
        {
            "text": {"type": "plain_text", "text": "LOI Accepted"},
            "value": "LOI Accepted",
        },
        {
            "text": {"type": "plain_text", "text": "Purchase Agreement Submitted"},
            "value": "Purchase Agreement Submitted",
        },
        {
            "text": {"type": "plain_text", "text": "Purchase Agreement Accepted"},
            "value": "Purchase Agreement Accepted",
        },
        {
            "text": {"type": "plain_text", "text": "Offer Not Made"},
            "value": "Offer Not Made",
        },
        {
            "text": {"type": "plain_text", "text": "Offer Not Accepted"},
            "value": "Offer Not Accepted",
        },
        {
            "text": {"type": "plain_text", "text": "Deal Didn't Close"},
            "value": "Deal Didn't Close",
        },
        {
            "text": {"type": "plain_text", "text": "Deal Closed"},
            "value": "Deal Closed",
        },
    ]


def open_deals_modal(user_id, team_id, trigger_id, view_id=None):

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "What are you looking to do?"},
            "accessory": {
                "type": "radio_buttons",
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Report New Deal",
                            "emoji": True,
                        },
                        "value": "reporting_new_deal",
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Update Existing Deal",
                            "emoji": True,
                        },
                        "value": "updating_existing_deal",
                    },
                ],
                "action_id": "deal_type",
            },
        }
    ]

    response = slack_client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "Deal Tracking"},
            "blocks": blocks,
            "close": {"type": "plain_text", "text": "Close"},
        },
    )


def new_deal_select_stage(user_id, team_id, trigger_id, view_id):

    is_open_or_closed = [
        # static select
        {
            "type": "input",
            "dispatch_action": True,
            "block_id": "new_deal_select_stage",
            "label": {
                "type": "plain_text",
                "text": "What stage is this deal in?",
            },
            "element": {
                "type": "static_select",
                "action_id": "new_deal_select_stage",
                "options": deal_stage_list_as_options(),
            },
        }
    ]

    response = slack_client.views_update(
        view_id=view_id,
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "Deal Tracking"},
            "blocks": is_open_or_closed,
            "close": {"type": "plain_text", "text": "Close"},
        },
    )


def submit_a_deal_review(
    user_id,
    team_id,
    trigger_id,
    view_id,
    deal_id=None,
    input_data={},
    updated_field=None,
    updated_value=None,
):

    # Deserialize state from private_metadata
    if isinstance(input_data, str) and input_data:
        input_data = json.loads(input_data)  # Convert JSON string to dictionary

    current_state = input_data or {}

    # Update the state with the latest field value
    if updated_field and updated_value is not None:
        current_state[updated_field] = updated_value

    blocks = [
        # radio button section
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Do you want to submit a deal review?",
            },
            "accessory": {
                "type": "radio_buttons",
                "action_id": "submit_a_deal_review",
                "options": [
                    {"text": {"type": "plain_text", "text": "Yes"}, "value": "Yes"},
                    {"text": {"type": "plain_text", "text": "No"}, "value": "No"},
                ],
            },
        }
    ]

    response = slack_client.views_update(
        view_id=view_id,
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "Deal Tracking"},
            "blocks": blocks,
            "close": {"type": "plain_text", "text": "Close"},
            "private_metadata": json.dumps(current_state),
        },
    )


def basic_deal_info_form(
    user_id,
    team_id,
    trigger_id,
    view_id,
    deal_id=None,
    input_data={},
    updated_field=None,
    updated_value=None,
):

    # Deserialize state from private_metadata
    if isinstance(input_data, str) and input_data:
        input_data = json.loads(input_data)  # Convert JSON string to dictionary

    current_state = input_data or {}

    # Update the state with the latest field value
    if updated_field and updated_value is not None:
        current_state[updated_field] = updated_value
    deal_id = current_state.get("deal_id")

    # - Business Type/Industry
    # - Business Description
    # - Company Name
    # - Annual Revenue
    # - Annual SDE
    deal_data = {}

    dictofoptions = {
        "Agriculture - Cannabis Businesses": "Agriculture - Cannabis Businesses",
        "Agriculture - Greenhouses / Tree Farms / Orchards": "Agriculture - Greenhouses / Tree Farms / Orchards",
        "Agriculture - Other": "Agriculture - Other",
        "Automotive and Boat - Auto Repair and Service Shops": "Automotive and Boat - Auto Repair and Service Shops",
        "Automotive and Boat - Car Dealerships / Motorcycle Businesses": "Automotive and Boat - Car Dealerships / Motorcycle Businesses",
        "Automotive and Boat - Car Washes": "Automotive and Boat - Car Washes",
        "Automotive and Boat - Equipment Rental and Dealers": "Automotive and Boat - Equipment Rental and Dealers",
        "Automotive and Boat - Gas Stations": "Automotive and Boat - Gas Stations",
        "Automotive and Boat - Other": "Automotive and Boat - Other",
        "Automotive and Boat - Towing Companies": "Automotive and Boat - Towing Companies",
        "Beauty and Personal Care - Beauty Salons / Barber Shops": "Beauty and Personal Care - Beauty Salons / Barber Shops",
        "Beauty and Personal Care - Massage / Spas": "Beauty and Personal Care - Massage / Spas",
        "Building and Construction - Building Material and Hardware Stores": "Building and Construction - Building Material and Hardware Stores",
        "Building and Construction - Carpet and Flooring Businesses": "Building and Construction - Carpet and Flooring Businesses",
        "Building and Construction - Concrete": "Building and Construction - Concrete",
        "Building and Construction - Electrical and Mechanical": "Building and Construction - Electrical and Mechanical",
        "Building and Construction - Fencing Businesses": "Building and Construction - Fencing Businesses",
        "Building and Construction - Heavy Construction": "Building and Construction - Heavy Construction",
        "Building and Construction - HVAC / Plumbing Businesses": "Building and Construction - HVAC / Plumbing Businesses",
        "Building and Construction - Painting Businesses": "Building and Construction - Painting Businesses",
        "Building and Construction - Roofing Business": "Building and Construction - Roofing Business",
        "Communication and Media - Magazines and Newspapers": "Communication and Media - Magazines and Newspapers",
        "Education and Children - Day Care and Child Care Centers": "Education and Children - Day Care and Child Care Centers",
        "Education and Children - Schools / Preschools": "Education and Children - Schools / Preschools",
        "Entertainment and Recreation - Services & Facilities": "Entertainment and Recreation - Services & Facilities",
        "Entertainment and Recreation - Other": "Entertainment and Recreation - Other",
        "Entertainment and Recreation - Outdoor Adventure Business": "Entertainment and Recreation - Outdoor Adventure Business",
        "Financial Services - Accounting and Tax Practices": "Financial Services - Accounting and Tax Practices",
        "Financial Services - Banking / Loans": "Financial Services - Banking / Loans",
        "Financial Services - Check Cashing": "Financial Services - Check Cashing",
        "Financial Services - Insurance Agencies": "Financial Services - Insurance Agencies",
        "Health Care & Fitness - Assisted Living / Nursing Homes / Home Health Care": "Health Care & Fitness - Assisted Living / Nursing Homes / Home Health Care",
        "Health Care & Fitness - Chiropractic Practices": "Health Care & Fitness - Chiropractic Practices",
        "Health Care & Fitness - Cosmetic Medical, Surgery & Med Spa": "Health Care & Fitness - Cosmetic Medical, Surgery & Med Spa",
        "Health Care & Fitness - Dance, Pilates and Yoga": "Health Care & Fitness - Dance, Pilates and Yoga",
        "Health Care & Fitness - Dental Practices": "Health Care & Fitness - Dental Practices",
        "Health Care & Fitness - Gyms and Fitness Centers": "Health Care & Fitness - Gyms and Fitness Centers",
        "Health Care & Fitness - Medical Practices": "Health Care & Fitness - Medical Practices",
        "Health Care & Fitness - Medical Transportation Businesses": "Health Care & Fitness - Medical Transportation Businesses",
        "Health Care & Fitness - Physical Therapy Practices": "Health Care & Fitness - Physical Therapy Practices",
        "Manufacturing - Clothing and Fabric": "Manufacturing - Clothing and Fabric",
        "Manufacturing - Food and Related products": "Manufacturing - Food and Related products",
        "Manufacturing - Furniture and Fixtures": "Manufacturing - Furniture and Fixtures",
        "Manufacturing - Lumber and Wood Products": "Manufacturing - Lumber and Wood Products",
        "Manufacturing - Other": "Manufacturing - Other",
        "Manufacturing - Packaging": "Manufacturing - Packaging",
        "Manufacturing - Paper / Printing": "Manufacturing - Paper / Printing",
        "Manufacturing - Sign Manufacturers": "Manufacturing - Sign Manufacturers",
        "Online & Technology - Cell Phone and Computer Repair and Services": "Online & Technology - Cell Phone and Computer Repair and Services",
        "Online & Technology - E-Commerce Stores": "Online & Technology - E-Commerce Stores",
        "Online & Technology - Graphic / Websites / Web Design": "Online & Technology - Graphic / Websites / Web Design",
        "Online & Technology - IT / Software / SaaS Businesses": "Online & Technology - IT / Software / SaaS Businesses",
        "Other - All Non-Classifiable Businesses": "Other - All Non-Classifiable Businesses",
        "Pet Services - Daycare, Boarding, Grooming / Pet Store and Supplies": "Pet Services - Daycare, Boarding, Grooming / Pet Store and Supplies",
        "Pet Services - Veterinary Practices": "Pet Services - Veterinary Practices",
        "Restaurants and Food - Bakeries / Donut Shops ": "Restaurants and Food - Bakeries / Donut Shops",
        "Restaurants and Food - Bars, Pubs and Taverns": "Restaurants and Food - Bars, Pubs and Taverns",
        "Restaurants and Food - Breweries / Distilleries": "Restaurants and Food - Breweries / Distilleries",
        "Restaurants and Food - Delis and Sandwich Shops": "Restaurants and Food - Delis and Sandwich Shops",
        "Restaurants and Food - Food Trucks": "Restaurants and Food - Food Trucks",
        "Restaurants + Food - Diners, Fast Food, Cafes, Coffee, Ice Cream": "Restaurants + Food - Diners, Fast Food, Cafes, Coffee, Ice Cream",
        "Retail - Beauty Supply Stores": "Retail - Beauty Supply Stores",
        "Retail - Bike Shops": "Retail - Bike Shops",
        "Retail - Clothing and Accessory Stores": "Retail - Clothing and Accessory Stores",
        "Retail - Convenience Stores": "Retail - Convenience Stores",
        "Retail - Flower Shops": "Retail - Flower Shops",
        "Retail - Furniture and Furnishings Stores / Antique Shops": "Retail - Furniture and Furnishings Stores / Antique Shops",
        "Retail - Grocery Stores and Supermarkets": "Retail - Grocery Stores and Supermarkets",
        "Retail - Jewelry Stores / Pawn Shops": "Retail - Jewelry Stores / Pawn Shops",
        "Retail - Liquor Stores": "Retail - Liquor Stores",
        "Retail - Other": "Retail - Other",
        "Retail - Pharmacies / Health Food and Nutrition": "Retail - Pharmacies / Health Food and Nutrition",
        "Retail - Sporting Goods Stores and Shooting Ranges": "Retail - Sporting Goods Stores and Shooting Ranges",
        "Retail - Vending Machines": "Retail - Vending Machines",
        "Service Businesses - Amazon / Fedex / UPS Stores / Shipping Routes": "Service Businesses - Amazon / Fedex / UPS Stores / Shipping Routes",
        "Service Businesses - Catering Companies": "Service Businesses - Catering Companies",
        "Service Businesses - Cleaning Businesses": "Service Businesses - Cleaning Businesses",
        "Service Businesses - Commercial Laundry / Laundromats and Coin Laundry": "Service Businesses - Commercial Laundry / Laundromats and Coin Laundry",
        "Service Businesses - Consulting Businesses": "Service Businesses - Consulting Businesses",
        "Service Businesses - Dry Cleaners": "Service Businesses - Dry Cleaners",
        "Service Businesses - Event Planning Businesses": "Service Businesses - Event Planning Businesses",
        "Service Businesses - Funeral Homes": "Service Businesses - Funeral Homes",
        "Service Businesses - Landscaping and Yard Services": "Service Businesses - Landscaping and Yard Services",
        "Service Businesses - Locksmith": "Service Businesses - Locksmith",
        "Service Businesses - Marketing and Advertising Businesses": "Service Businesses - Marketing and Advertising Businesses",
        "Service Businesses - Other": "Service Businesses - Other",
        "Service Businesses - Pest Control": "Service Businesses - Pest Control",
        "Service Businesses - Photography Businesses": "Service Businesses - Photography Businesses",
        "Service Businesses - Property Management": "Service Businesses - Property Management",
        "Service Businesses - Security": "Service Businesses - Security",
        "Service Businesses - Staffing Agencies": "Service Businesses - Staffing Agencies",
        "Service Businesses - Tutoring Businesses": "Service Businesses - Tutoring Businesses",
        "Service Businesses - Water Businesses and Stores": "Service Businesses - Water Businesses and Stores",
        "Transportation and Storage - Limo and Passenger Transportation": "Transportation and Storage - Limo and Passenger Transportation",
        "Transportation and Storage - Moving and Shipping": "Transportation and Storage - Moving and Shipping",
        "Transportation and Storage - Storage Facilities and Warehouses": "Transportation and Storage - Storage Facilities and Warehouses",
        "Travel - Campgrounds / RV Parks / Mobile Home Parks": "Travel - Campgrounds / RV Parks / Mobile Home Parks",
        "Travel - Hotels / Motels / Bed & Breakfast": "Travel - Hotels / Motels / Bed & Breakfast",
        "Travel - Travel Agencies": "Travel - Travel Agencies",
        "Wholesale and Distributors - Durable / Nondurable Goods": "Wholesale and Distributors - Durable / Nondurable Goods",
    }

    businessindustryoptions = []
    if deal_id:
        print("deal id is ", deal_id)

        deal_data = deal_data_from_hubspot(deal_id)  # Fetch data from HubSpot
        print(len(deal_data))
    for key, value in dictofoptions.items():
        # which key is over 75 characters
        if len(key) > 75:
            print("key is over 75 characters", key)
        key = key[:75]  # Ensure keys are <= 75 characters
        businessindustryoptions.append(
            {
                "text": {"type": "plain_text", "text": str(key)},
                "value": str(value),
            }
        )

    def get_initial_value(field):
        print(deal_data.get(field))
        """Helper to retrieve initial value from deal_data."""
        if deal_data.get(field) is not None:
            return str(deal_data.get(field))
        return " "

    def get_initial_option(field):
        """Helper to create initial_option for dropdowns and radio buttons."""
        value = deal_data.get(field)
        if value is not None:
            return {
                "text": {"type": "plain_text", "text": str(value), "emoji": True},
                "value": str(value),
            }
        return None

    blocks = [
        {
            "type": "input",
            "block_id": "business_type",
            "label": {"type": "plain_text", "text": "Business Type/Industry"},
            "element": {
                "type": "static_select",
                "action_id": "business_type",
                **(
                    {"initial_option": get_initial_option("business_type_industry")}
                    if "business_type_industry" in deal_data
                    and deal_data.get("business_type_industry") is not None
                    else {}
                ),
                "placeholder": {"type": "plain_text", "text": "Select an option"},
                "options": businessindustryoptions,
            },
        },
        {
            "type": "input",
            "block_id": "business_description",
            "label": {"type": "plain_text", "text": "Business Description"},
            "element": {
                "type": "plain_text_input",
                "action_id": "business_description",
                **(
                    {"initial_value": get_initial_value("deal_name___description")}
                    if "deal_name___description" in deal_data
                    and deal_data.get("deal_name___description") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Example: Landscaping Business in Phoenix or $1.1M HVAC Company.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "company_name",
            "label": {"type": "plain_text", "text": "Company Name"},
            "element": {
                "type": "plain_text_input",
                "action_id": "company_name",
                **(
                    {"initial_value": get_initial_value("company_name")}
                    if "company_name" in deal_data
                    and deal_data.get("company_name") is not None
                    else {}
                ),
            },
            "hint": {
                "type": "plain_text",
                "text": "Feel free to list N/A or similar if you don't want to share at this time.",
            },
        },
        {
            "type": "input",
            "block_id": "annual_revenue",
            "label": {"type": "plain_text", "text": "What is the annual revenue?"},
            "element": {
                "type": "number_input",
                "is_decimal_allowed": False,
                "action_id": "annual_revenue",
                **(
                    {"initial_value": get_initial_value("annual_revenue")}
                    if "annual_revenue" in deal_data
                    and deal_data.get("annual_revenue") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter a number without commas or dollar signs!",
                },
            },
        },
        {
            "type": "input",
            "block_id": "profit_sde_ebitda",
            "label": {
                "type": "plain_text",
                "text": "What is the annual profit, SDE, EBITDA?",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "profit_sde_ebitda",
                **(
                    {
                        "initial_value": str(
                            deal_data.get("what_is_the_annual_profit", "")
                        )
                    }
                    if "what_is_the_annual_profit" in deal_data
                    and deal_data.get("what_is_the_annual_profit") is not None
                    else {}
                ),
            },
        },
    ]

    slack_client.views_update(
        view_id=view_id,
        view={
            "type": "modal",
            "private_metadata": json.dumps(current_state),
            "callback_id": "basic_deal_info_form",
            "title": {"type": "plain_text", "text": "Deal Tracking"},
            "blocks": blocks,
            "close": {"type": "plain_text", "text": "Close"},
            "submit": {"type": "plain_text", "text": "Save"},
        },
    )


def existing_deal_select_stage(user_id, team_id, trigger_id, view_id, deal_id=None):

    usersdeals = []
    listofusersrecords = get_hubspot_comm_acquisition_records(user_id)
    for record in listofusersrecords:
        clean_name = f"{record[1]} - {record[3]}"  # max 75 characters
        if len(clean_name) > 75:
            clean_name = clean_name[:75]
        usersdeals.append(
            {
                "text": {"type": "plain_text", "text": clean_name},
                "value": record[0],
            }
        )

    selectdeal = [
        {
            "type": "input",
            "dispatch_action": True,
            "block_id": "select_deal_id",
            "label": {
                "type": "plain_text",
                "text": "Which deal are you looking to update?",
            },
            "element": {
                "type": "static_select",
                "action_id": "select_deal_id",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select a deal",
                },
                "options": usersdeals,
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Looking to update a deal that is not listed? Please contact reach out in <#C05GSU14KS7>.",
                }
            ],
        },
    ]

    selectstage = [
        {
            "type": "input",
            "dispatch_action": True,
            "block_id": f"existing_deal_select_deal_stage|{deal_id}",
            "label": {
                "type": "plain_text",
                "text": "What stage is this deal in?",
            },
            "element": {
                "type": "static_select",
                "action_id": f"existing_deal_select_deal_stage|{deal_id}",
                "options": deal_stage_list_as_options(),
            },
        },
    ]

    blocks = []
    if deal_id is not None:
        blocks = selectstage
    else:
        blocks = selectdeal

    response = slack_client.views_update(
        view_id=view_id,
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "Deal Tracking"},
            "blocks": blocks,
            "close": {"type": "plain_text", "text": "Close"},
            "submit": {"type": "plain_text", "text": "Next"},
        },
    )


def deal_review_form_modal(
    user_id,
    team_id,
    trigger_id,
    view_id,
    deal_stage,
    deal_id=None,
):
    # Header Section
    header = []
    deal_data = {}
    if deal_id:
        header.append(
            {
                "type": "section",
                "block_id": "info",
                "text": {
                    "type": "mrkdwn",
                    "text": f"You are currently updating your Deal ID: {deal_id}",
                },
            }
        )
        header.append({"type": "divider"})
        deal_data = deal_data_from_hubspot(deal_id)  # Fetch data from HubSpot

    def get_initital_value_number(field):
        if deal_data.get(field):
            return int(deal_data.get(field))
        else:
            return 0

    def get_initial_options(field):
        value = deal_data.get(field)
        print("value is ----->", value)
        options = []
        if value is not None:
            # str is "Cash;SBA Loan;Seller Financing;Other Loan;Retirement Funds;Heloc;Outside Capital"
            # split by ;
            values = value.split(";")

            for item in values:
                # Handle special case for HELOC/Heloc
                if item.lower() == "heloc":
                    item = "Heloc"

                options.append(
                    {
                        "text": {
                            "type": "plain_text",
                            "text": str(item),
                        },
                        "value": str(item),
                    }
                )
        pprint(options)
        return options

    def get_initial_value(field):
        """Helper to retrieve initial value from deal_data."""
        if deal_data.get(field) is not None:
            return str(deal_data.get(field))
        return " "

    def get_initial_option(field):
        """Helper to create initial_option for dropdowns and radio buttons."""
        value = deal_data.get(field)
        if value is not None:
            return {
                "text": {"type": "plain_text", "text": str(value), "emoji": True},
                "value": str(value),
            }
        return None

    # Industry Options
    businessindustryoptions = []

    dictofoptions = {
        "Agriculture - Cannabis Businesses": "Agriculture - Cannabis Businesses",
        "Agriculture - Greenhouses / Tree Farms / Orchards": "Agriculture - Greenhouses / Tree Farms / Orchards",
        "Agriculture - Other": "Agriculture - Other",
        "Automotive and Boat - Auto Repair and Service Shops": "Automotive and Boat - Auto Repair and Service Shops",
        "Automotive and Boat - Car Dealerships / Motorcycle Businesses": "Automotive and Boat - Car Dealerships / Motorcycle Businesses",
        "Automotive and Boat - Car Washes": "Automotive and Boat - Car Washes",
        "Automotive and Boat - Equipment Rental and Dealers": "Automotive and Boat - Equipment Rental and Dealers",
        "Automotive and Boat - Gas Stations": "Automotive and Boat - Gas Stations",
        "Automotive and Boat - Other": "Automotive and Boat - Other",
        "Automotive and Boat - Towing Companies": "Automotive and Boat - Towing Companies",
        "Beauty and Personal Care - Beauty Salons / Barber Shops": "Beauty and Personal Care - Beauty Salons / Barber Shops",
        "Beauty and Personal Care - Massage / Spas": "Beauty and Personal Care - Massage / Spas",
        "Building and Construction - Building Material and Hardware Stores": "Building and Construction - Building Material and Hardware Stores",
        "Building and Construction - Carpet and Flooring Businesses": "Building and Construction - Carpet and Flooring Businesses",
        "Building and Construction - Concrete": "Building and Construction - Concrete",
        "Building and Construction - Electrical and Mechanical": "Building and Construction - Electrical and Mechanical",
        "Building and Construction - Fencing Businesses": "Building and Construction - Fencing Businesses",
        "Building and Construction - Heavy Construction": "Building and Construction - Heavy Construction",
        "Building and Construction - HVAC / Plumbing Businesses": "Building and Construction - HVAC / Plumbing Businesses",
        "Building and Construction - Painting Businesses": "Building and Construction - Painting Businesses",
        "Building and Construction - Roofing Business": "Building and Construction - Roofing Business",
        "Communication and Media - Magazines and Newspapers": "Communication and Media - Magazines and Newspapers",
        "Education and Children - Day Care and Child Care Centers": "Education and Children - Day Care and Child Care Centers",
        "Education and Children - Schools / Preschools": "Education and Children - Schools / Preschools",
        "Entertainment and Recreation - Services & Facilities": "Entertainment and Recreation - Services & Facilities",
        "Entertainment and Recreation - Other": "Entertainment and Recreation - Other",
        "Entertainment and Recreation - Outdoor Adventure Business": "Entertainment and Recreation - Outdoor Adventure Business",
        "Financial Services - Accounting and Tax Practices": "Financial Services - Accounting and Tax Practices",
        "Financial Services - Banking / Loans": "Financial Services - Banking / Loans",
        "Financial Services - Check Cashing": "Financial Services - Check Cashing",
        "Financial Services - Insurance Agencies": "Financial Services - Insurance Agencies",
        "Health Care & Fitness - Assisted Living / Nursing Homes / Home Health Care": "Health Care & Fitness - Assisted Living / Nursing Homes / Home Health Care",
        "Health Care & Fitness - Chiropractic Practices": "Health Care & Fitness - Chiropractic Practices",
        "Health Care & Fitness - Cosmetic Medical, Surgery & Med Spa": "Health Care & Fitness - Cosmetic Medical, Surgery & Med Spa",
        "Health Care & Fitness - Dance, Pilates and Yoga": "Health Care & Fitness - Dance, Pilates and Yoga",
        "Health Care & Fitness - Dental Practices": "Health Care & Fitness - Dental Practices",
        "Health Care & Fitness - Gyms and Fitness Centers": "Health Care & Fitness - Gyms and Fitness Centers",
        "Health Care & Fitness - Medical Practices": "Health Care & Fitness - Medical Practices",
        "Health Care & Fitness - Medical Transportation Businesses": "Health Care & Fitness - Medical Transportation Businesses",
        "Health Care & Fitness - Physical Therapy Practices": "Health Care & Fitness - Physical Therapy Practices",
        "Manufacturing - Clothing and Fabric": "Manufacturing - Clothing and Fabric",
        "Manufacturing - Food and Related products": "Manufacturing - Food and Related products",
        "Manufacturing - Furniture and Fixtures": "Manufacturing - Furniture and Fixtures",
        "Manufacturing - Lumber and Wood Products": "Manufacturing - Lumber and Wood Products",
        "Manufacturing - Other": "Manufacturing - Other",
        "Manufacturing - Packaging": "Manufacturing - Packaging",
        "Manufacturing - Paper / Printing": "Manufacturing - Paper / Printing",
        "Manufacturing - Sign Manufacturers": "Manufacturing - Sign Manufacturers",
        "Online & Technology - Cell Phone and Computer Repair and Services": "Online & Technology - Cell Phone and Computer Repair and Services",
        "Online & Technology - E-Commerce Stores": "Online & Technology - E-Commerce Stores",
        "Online & Technology - Graphic / Websites / Web Design": "Online & Technology - Graphic / Websites / Web Design",
        "Online & Technology - IT / Software / SaaS Businesses": "Online & Technology - IT / Software / SaaS Businesses",
        "Other - All Non-Classifiable Businesses": "Other - All Non-Classifiable Businesses",
        "Pet Services - Daycare, Boarding, Grooming / Pet Store and Supplies": "Pet Services - Daycare, Boarding, Grooming / Pet Store and Supplies",
        "Pet Services - Veterinary Practices": "Pet Services - Veterinary Practices",
        "Restaurants and Food - Bakeries / Donut Shops ": "Restaurants and Food - Bakeries / Donut Shops",
        "Restaurants and Food - Bars, Pubs and Taverns": "Restaurants and Food - Bars, Pubs and Taverns",
        "Restaurants and Food - Breweries / Distilleries": "Restaurants and Food - Breweries / Distilleries",
        "Restaurants and Food - Delis and Sandwich Shops": "Restaurants and Food - Delis and Sandwich Shops",
        "Restaurants and Food - Food Trucks": "Restaurants and Food - Food Trucks",
        "Restaurants + Food - Diners, Fast Food, Cafes, Coffee, Ice Cream": "Restaurants + Food - Diners, Fast Food, Cafes, Coffee, Ice Cream",
        "Retail - Beauty Supply Stores": "Retail - Beauty Supply Stores",
        "Retail - Bike Shops": "Retail - Bike Shops",
        "Retail - Clothing and Accessory Stores": "Retail - Clothing and Accessory Stores",
        "Retail - Convenience Stores": "Retail - Convenience Stores",
        "Retail - Flower Shops": "Retail - Flower Shops",
        "Retail - Furniture and Furnishings Stores / Antique Shops": "Retail - Furniture and Furnishings Stores / Antique Shops",
        "Retail - Grocery Stores and Supermarkets": "Retail - Grocery Stores and Supermarkets",
        "Retail - Jewelry Stores / Pawn Shops": "Retail - Jewelry Stores / Pawn Shops",
        "Retail - Liquor Stores": "Retail - Liquor Stores",
        "Retail - Other": "Retail - Other",
        "Retail - Pharmacies / Health Food and Nutrition": "Retail - Pharmacies / Health Food and Nutrition",
        "Retail - Sporting Goods Stores and Shooting Ranges": "Retail - Sporting Goods Stores and Shooting Ranges",
        "Retail - Vending Machines": "Retail - Vending Machines",
        "Service Businesses - Amazon / Fedex / UPS Stores / Shipping Routes": "Service Businesses - Amazon / Fedex / UPS Stores / Shipping Routes",
        "Service Businesses - Catering Companies": "Service Businesses - Catering Companies",
        "Service Businesses - Cleaning Businesses": "Service Businesses - Cleaning Businesses",
        "Service Businesses - Commercial Laundry / Laundromats and Coin Laundry": "Service Businesses - Commercial Laundry / Laundromats and Coin Laundry",
        "Service Businesses - Consulting Businesses": "Service Businesses - Consulting Businesses",
        "Service Businesses - Dry Cleaners": "Service Businesses - Dry Cleaners",
        "Service Businesses - Event Planning Businesses": "Service Businesses - Event Planning Businesses",
        "Service Businesses - Funeral Homes": "Service Businesses - Funeral Homes",
        "Service Businesses - Landscaping and Yard Services": "Service Businesses - Landscaping and Yard Services",
        "Service Businesses - Locksmith": "Service Businesses - Locksmith",
        "Service Businesses - Marketing and Advertising Businesses": "Service Businesses - Marketing and Advertising Businesses",
        "Service Businesses - Other": "Service Businesses - Other",
        "Service Businesses - Pest Control": "Service Businesses - Pest Control",
        "Service Businesses - Photography Businesses": "Service Businesses - Photography Businesses",
        "Service Businesses - Property Management": "Service Businesses - Property Management",
        "Service Businesses - Security": "Service Businesses - Security",
        "Service Businesses - Staffing Agencies": "Service Businesses - Staffing Agencies",
        "Service Businesses - Tutoring Businesses": "Service Businesses - Tutoring Businesses",
        "Service Businesses - Water Businesses and Stores": "Service Businesses - Water Businesses and Stores",
        "Transportation and Storage - Limo and Passenger Transportation": "Transportation and Storage - Limo and Passenger Transportation",
        "Transportation and Storage - Moving and Shipping": "Transportation and Storage - Moving and Shipping",
        "Transportation and Storage - Storage Facilities and Warehouses": "Transportation and Storage - Storage Facilities and Warehouses",
        "Travel - Campgrounds / RV Parks / Mobile Home Parks": "Travel - Campgrounds / RV Parks / Mobile Home Parks",
        "Travel - Hotels / Motels / Bed & Breakfast": "Travel - Hotels / Motels / Bed & Breakfast",
        "Travel - Travel Agencies": "Travel - Travel Agencies",
        "Wholesale and Distributors - Durable / Nondurable Goods": "Wholesale and Distributors - Durable / Nondurable Goods",
    }

    for key, value in dictofoptions.items():
        if len(key) > 75:
            print("key is over 75 characters", key)
        key = key[:75]  # Ensure keys are <= 75 characters
        businessindustryoptions.append(
            {
                "text": {"type": "plain_text", "text": str(key)},
                "value": str(value),
            }
        )

    # Form Fields
    questionblocks = [
        {
            "type": "input",
            "block_id": "company_name",
            "label": {"type": "plain_text", "text": "Company Name"},
            "element": {
                "type": "plain_text_input",
                "action_id": "company_name",
                **(
                    {"initial_value": get_initial_value("company_name")}
                    if "company_name" in deal_data
                    and deal_data.get("company_name") is not None
                    else {}
                ),
                "placeholder": {"type": "plain_text", "text": "Acme Co."},
            },
            "hint": {
                "type": "plain_text",
                "text": "Feel free to list N/A or similar if you don't want to share at this time.",
            },
        },
        {
            "type": "input",
            "block_id": "share_mnl",
            "label": {
                "type": "plain_text",
                "text": "Are you willing to share this on MNL?",
            },
            "element": {
                "type": "static_select",
                "action_id": "share_mnl",
                "placeholder": {"type": "plain_text", "text": "Select an option"},
                **(
                    {
                        "initial_option": get_initial_option(
                            "are_you_willing_to_share_this_on_mnl_"
                        )
                    }
                    if "are_you_willing_to_share_this_on_mnl_" in deal_data
                    and deal_data.get("are_you_willing_to_share_this_on_mnl_")
                    is not None
                    else {}
                ),
                "options": [
                    {"text": {"type": "plain_text", "text": "Yes"}, "value": "Yes"},
                    {"text": {"type": "plain_text", "text": "No"}, "value": "No"},
                ],
            },
        },
        {
            "type": "input",
            "block_id": "business_type",
            "label": {"type": "plain_text", "text": "Business Type/Industry"},
            "element": {
                "type": "static_select",
                "action_id": "business_type",
                **(
                    {"initial_option": get_initial_option("business_type_industry")}
                    if "business_type_industry" in deal_data
                    and deal_data.get("business_type_industry") is not None
                    else {}
                ),
                "placeholder": {"type": "plain_text", "text": "Select an option"},
                "options": businessindustryoptions,
            },
        },
        {
            "type": "input",
            "block_id": "business_description",
            "label": {"type": "plain_text", "text": "Business Description"},
            "element": {
                "type": "plain_text_input",
                "action_id": "business_description",
                **(
                    {"initial_value": get_initial_value("deal_name___description")}
                    if "deal_name___description" in deal_data
                    and deal_data.get("deal_name___description") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Example: Landscaping Business in Phoenix or $1.1M HVAC Company.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "location",
            "optional": True,
            "label": {"type": "plain_text", "text": "Location of the Business"},
            "element": {
                "type": "plain_text_input",
                "action_id": "location",
                **(
                    {"initial_value": get_initial_value("location_of_the_business")}
                    if "location_of_the_business" in deal_data
                    and deal_data.get("location_of_the_business") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "You may leave this blank if you prefer not to disclose.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "earnings_type",
            "label": {
                "type": "plain_text",
                "text": "Are you providing SDE or EBITDA for earnings?",
            },
            "element": {
                "type": "static_select",
                "action_id": "earnings_type",
                "placeholder": {"type": "plain_text", "text": "Select an option"},
                **(
                    {
                        "initial_option": get_initial_option(
                            "are_you_providing_sde_or_ebitda_for_earnings___please_specify_which_one_"
                        )
                    }
                    if "are_you_providing_sde_or_ebitda_for_earnings___please_specify_which_one_"
                    in deal_data
                    and deal_data.get(
                        "are_you_providing_sde_or_ebitda_for_earnings___please_specify_which_one_"
                    )
                    is not None
                    else {}
                ),
                "options": [
                    {"text": {"type": "plain_text", "text": "SDE"}, "value": "SDE"},
                    {
                        "text": {"type": "plain_text", "text": "EBITDA"},
                        "value": "EBITDA",
                    },
                ],
            },
        },
        {
            "type": "input",
            "block_id": "sde_ebitda_2024",
            "label": {"type": "plain_text", "text": "2024 SDE / EBITDA"},
            "element": {
                "type": "plain_text_input",
                "action_id": "sde_ebitda_2024",
                **(
                    {"initial_value": get_initial_value("n2024_sde___ebitda")}
                    if "n2024_sde___ebitda" in deal_data
                    and deal_data.get("n2024_sde___ebitda") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Put NA if not available.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "sde_ebitda_2023",
            "label": {"type": "plain_text", "text": "2023 SDE / EBITDA"},
            "element": {
                "type": "plain_text_input",
                "action_id": "sde_ebitda_2023",
                **(
                    {"initial_value": get_initial_value("n2023_sde___ebitda")}
                    if "n2023_sde___ebitda" in deal_data
                    and deal_data.get("n2023_sde___ebitda") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Put NA if not available.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "sde_ebitda_2022",
            "label": {"type": "plain_text", "text": "2022 SDE / EBITDA"},
            "element": {
                "type": "plain_text_input",
                "action_id": "sde_ebitda_2022",
                **(
                    {"initial_value": get_initial_value("n2022_sde___ebitda")}
                    if "n2022_sde___ebitda" in deal_data
                    and deal_data.get("n2022_sde___ebitda") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Put NA if not available.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "sde_ebitda_2021",
            "label": {"type": "plain_text", "text": "2021 SDE / EBITDA"},
            "element": {
                "type": "plain_text_input",
                "action_id": "sde_ebitda_2021",
                **(
                    {"initial_value": get_initial_value("n2021_sde___ebitda")}
                    if "n2021_sde___ebitda" in deal_data
                    and deal_data.get("n2021_sde___ebitda") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Put NA if not available.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "revenue_2024",
            "label": {"type": "plain_text", "text": "2024 Revenue"},
            "element": {
                "type": "plain_text_input",
                "action_id": "revenue_2024",
                **(
                    {"initial_value": get_initial_value("n2024_revenue")}
                    if "n2024_revenue" in deal_data
                    and deal_data.get("n2024_revenue") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Put NA if not available.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "revenue_2023",
            "label": {"type": "plain_text", "text": "2023 Revenue"},
            "element": {
                "type": "plain_text_input",
                "action_id": "revenue_2023",
                **(
                    {"initial_value": get_initial_value("n2023_revenue")}
                    if "n2023_revenue" in deal_data
                    and deal_data.get("n2023_revenue") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Put NA if not available.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "revenue_2022",
            "label": {"type": "plain_text", "text": "2022 Revenue"},
            "element": {
                "type": "plain_text_input",
                "action_id": "revenue_2022",
                **(
                    {"initial_value": get_initial_value("n2022_revenue")}
                    if "n2022_revenue" in deal_data
                    and deal_data.get("n2022_revenue") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Put NA if not available.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "revenue_2021",
            "label": {"type": "plain_text", "text": "2021 Revenue"},
            "element": {
                "type": "plain_text_input",
                "action_id": "revenue_2021",
                **(
                    {"initial_value": get_initial_value("n2021_revenue")}
                    if "n2021_revenue" in deal_data
                    and deal_data.get("n2021_revenue") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Put NA if not available.",
                },
            },
        },
        {
            "type": "input",
            "block_id": "asking_price",
            "label": {"type": "plain_text", "text": "Asking Price"},
            "element": {
                "type": "number_input",
                "action_id": "asking_price",
                "is_decimal_allowed": False,
                **(
                    {"initial_value": get_initial_value("deal_purchase_price")}
                    if "deal_purchase_price" in deal_data
                    and deal_data.get("deal_purchase_price") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter a number without commas or dollar signs!",
                },
            },
        },
        {
            "type": "input",
            "block_id": "purchase_price",
            "label": {"type": "plain_text", "text": "Proposed Purchase Price"},
            "element": {
                "type": "plain_text_input",
                "action_id": "purchase_price",
                **(
                    {"initial_value": get_initial_value("proposed_purchase_price")}
                    if "proposed_purchase_price" in deal_data
                    and deal_data.get("proposed_purchase_price") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter a number without commas or dollar signs!",
                },
            },
        },
        {
            "type": "input",
            "block_id": "finance_type",
            "label": {
                "type": "plain_text",
                "text": "Share how you intend to finance the deal",
            },
            "element": {
                "type": "multi_static_select",
                "action_id": "finance_type",
                **(
                    {"initial_options": get_initial_options("financing_method")}
                    if "financing_method" in deal_data
                    and deal_data.get("financing_method") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select an option",
                },
                "options": [
                    {
                        "text": {"type": "plain_text", "text": "Cash"},
                        "value": "Cash",
                    },
                    {
                        "text": {"type": "plain_text", "text": "SBA Loan"},
                        "value": "SBA Loan",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Other Loan"},
                        "value": "Other Loan",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Seller Financing"},
                        "value": "Seller Financing",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Retirement Funds"},
                        "value": "Retirement Funds",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Heloc"},
                        "value": "Heloc",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Outside Capital"},
                        "value": "Outside Capital",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Other"},
                        "value": "Other",
                    },
                ],
            },
        },
        {
            "type": "input",
            "block_id": "owner_details",
            "label": {"type": "plain_text", "text": "Owner Details"},
            "element": {
                "type": "plain_text_input",
                "multiline": True,
                "action_id": "owner_details",
                **(
                    {"initial_value": get_initial_value("owner_details__if_any_")}
                    if "owner_details__if_any_" in deal_data
                    and deal_data.get("owner_details__if_any_") is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "real_estate_percentage",
            "label": {
                "type": "plain_text",
                "text": "How much of the purchase price is for real estate?",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "real_estate_percentage",
                **(
                    {
                        "initial_value": get_initial_value(
                            "how_much_of_the_purchase_price_is_for_real_estate_"
                        )
                    }
                    if "how_much_of_the_purchase_price_is_for_real_estate_" in deal_data
                    and deal_data.get(
                        "how_much_of_the_purchase_price_is_for_real_estate_"
                    )
                    is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "additional_notes",
            "label": {
                "type": "plain_text",
                "text": "Additional Notes (equipment, employees, why you like the deal)",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "additional_notes",
                "multiline": True,
                **(
                    {
                        "initial_value": get_initial_value(
                            "additional_notes__equipment__employees__why_you_like_the_deal_"
                        )
                    }
                    if "additional_notes__equipment__employees__why_you_like_the_deal_"
                    in deal_data
                    and deal_data.get(
                        "additional_notes__equipment__employees__why_you_like_the_deal_"
                    )
                    is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "concerns_questions",
            "label": {
                "type": "plain_text",
                "text": "What are your main concerns or questions?",
            },
            "element": {
                "type": "plain_text_input",
                "multiline": True,
                "action_id": "concerns_questions",
                **(
                    {
                        "initial_value": get_initial_value(
                            "what_are_your_main_concerns_or_questions_"
                        )
                    }
                    if "what_are_your_main_concerns_or_questions_" in deal_data
                    and deal_data.get("what_are_your_main_concerns_or_questions_")
                    is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "file_input",
            "label": {
                "type": "plain_text",
                "text": "Please attach 1-3 years P&L and/or taxes. Ideally, upload a spreadsheet with the P&Ls year-by-year all in one sheet.",
            },
            "element": {
                "type": "file_input",
                "action_id": "file_input",
                "filetypes": ["jpg", "png", "gif", "jpeg", "pdf"],
                "max_files": 5,
            },
            "hint": {
                "type": "plain_text",
                "text": "You can upload .png, .jpg, .jpeg, or .pdf files.",
            },
        },
        {
            "type": "input",
            "block_id": "deal_calculator_ready",
            "element": {
                "type": "checkboxes",
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "Yes my deal calculator is ready",
                            "emoji": True,
                        },
                        "value": "True",
                    }
                ],
                "action_id": "deal_calculator_ready",
            },
            "label": {
                "type": "plain_text",
                "text": "Please note that the deal calculator is required. If it is not yet available, kindly close this form and return when ready.",
                "emoji": True,
            },
        },
        {
            "type": "input",
            "block_id": "deal_calculator_link",
            "label": {
                "type": "plain_text",
                "text": "Link to your deal calculator",
            },
            "hint": {
                "type": "plain_text",
                "text": "Please make sure the file is shared publicly with Read Only access. Alternatively, you can upload a screenshot above.",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "deal_calculator_link",
                **(
                    {"initial_value": get_initial_value("link_to_your_deal_calculator")}
                    if "link_to_your_deal_calculator" in deal_data
                    and deal_data.get("link_to_your_deal_calculator") is not None
                    else {}
                ),
            },
            "optional": True,
        },
                {
            "type": "input",
            "block_id": "sde_calculator_link",
            "label": {
                "type": "plain_text",
                "text": "Link to your SDE calculator",
            },
            "hint": {
                "type": "plain_text",
                "text": "Please make sure the file is shared publicly with Read Only access. Alternatively, you can upload a screenshot above.",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "sde_calculator_link",
                **(
                    {"initial_value": get_initial_value("sde_calculator_link")}
                    if "link_to_your_deal_calculator" in deal_data
                    and deal_data.get("sde_calculator_link") is not None
                    else {}
                ),
            },
            "optional": True,
        },
    ]

    # Combine header and questions
    blocks = header + questionblocks

    # Update Slack modal
    try:
        response = slack_client.views_update(
            view_id=view_id,
            view={
                "type": "modal",
                "blocks": blocks,
                "close": {"type": "plain_text", "text": "Close"},
                "submit": {"type": "plain_text", "text": "Submit"},
                "title": {"type": "plain_text", "text": "Deal Review Form"},
                "callback_id": "deal_review_form",
                "private_metadata": f"{deal_id}|{deal_stage}",
            },
        )
    except Exception as e:
        logging.error(f"Failed to open loading modal: {e}")
        return None
    print("Deal review form modal opened")


def deal_closed_form_modal(
    user_id,
    team_id,
    trigger_id,
    view_id,
    input_data={},
    updated_field=None,
    updated_value=None,
):
    # Deserialize state from private_metadata
    if isinstance(input_data, str) and input_data:
        input_data = json.loads(input_data)  # Convert JSON string to dictionary

    current_state = input_data or {}

    # Update the state with the latest field value
    if updated_field and updated_value is not None:
        current_state[updated_field] = updated_value

    print("new current state is", current_state)

    deal_id = current_state.get("deal_id")
    pay_type = current_state.get("pay_type")
    acquire_deal_before_or_after_joining = current_state.get(
        "acquire_deal_before_or_after_joining"
    )

    header = []
    deal_data = {}
    if deal_id:
        header.append(
            {
                "type": "section",
                "block_id": "info",
                "text": {
                    "type": "mrkdwn",
                    "text": f"You are currently updating your Deal ID: {deal_id}",
                },
            }
        )
        header.append({"type": "divider"})
        deal_data = deal_data_from_hubspot(deal_id)

    def get_initial_date(field):
        # structure as yyyy-mm-dd
        if field in deal_data and deal_data.get(field) is not None:
            return deal_data[field]
        return datetime.now().strftime("%Y-%m-%d")

    def get_initial_value(field):
        """Helper to get initial value from deal_data or current_state."""
        if current_state.get(field) is not None:
            return current_state.get(field)
        elif deal_data.get(field) is not None:
            return deal_data.get(field)
        else:
            return " "

    def initial_value_number(field):
        if current_state.get(field) is not None:
            return current_state.get(field)
        elif deal_data.get(field) is not None:
            return deal_data.get(field)
        else:
            return 0

    def get_initial_options(field):
        value = current_state.get(field) or deal_data.get(field)
        print("value is ----->", value)
        options = []
        if value is not None:
            # str is "Cash;SBA Loan;Seller Financing;Other Loan;Retirement Funds;Heloc;Outside Capital"
            # split by ;
            values = value.split(";")

            for item in values:
                # Handle special case for HELOC/Heloc
                if item.lower() == "heloc":
                    item = "Heloc"

                options.append(
                    {
                        "text": {
                            "type": "plain_text",
                            "text": str(item),
                        },
                        "value": str(item),
                    }
                )
        pprint(options)
        return options

    def get_initial_option(field):
        """Helper to create initial_option for dropdowns and radio buttons."""
        value = current_state.get(field) or deal_data.get(field)
        if value is not None:
            return {
                "text": {"type": "plain_text", "text": str(value), "emoji": True},
                "value": str(value),
            }
        return None

    inputfields = [
        {
            "type": "input",
            "block_id": "company_name",
            "label": {
                "type": "plain_text",
                "text": "Company Name",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "company_name",
                **(
                    {"initial_value": get_initial_value("company_name")}
                    if "company_name" in deal_data
                    and deal_data.get("company_name") is not None
                    else {}
                ),
            },
            "hint": {
                "type": "plain_text",
                "text": "Feel free to list N/A or similar if you don't want to share at this time.",
            },
        },
        {
            "type": "input",
            "block_id": "source",
            "label": {
                "type": "plain_text",
                "text": "Where'd you find/source this deal?",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "source",
                **(
                    {
                        "initial_value": get_initial_value(
                            "where_d_you_find_source_this_deal_"
                        )
                    }
                    if "where_d_you_find_source_this_deal_" in deal_data
                    and deal_data.get("where_d_you_find_source_this_deal_") is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "website",
            "optional": True,
            "label": {
                "type": "plain_text",
                "text": "What is the website? (if applicable)",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "website",
                **(
                    {"initial_value": get_initial_value("what_is_the_website_")}
                    if "what_is_the_website_" in deal_data
                    and deal_data.get("what_is_the_website_") is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "date_closed",
            "label": {"type": "plain_text", "text": "What is the date you closed?"},
            "element": {
                "type": "datepicker",
                "action_id": "date_closed",
                "initial_date": get_initial_date("deal_closed"),
                "placeholder": {"type": "plain_text", "text": "MM/DD/YYYY"},
            },
        },
        {
            "type": "input",
            "block_id": "purchase_price",
            "label": {"type": "plain_text", "text": "What was the purchase price?"},
            "element": {
                "type": "number_input",
                "action_id": "purchase_price",
                "is_decimal_allowed": False,
                **(
                    {"initial_value": initial_value_number("purchase_price")}
                    if "purchase_price" in deal_data
                    and deal_data.get("purchase_price") is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "annual_revenue",
            "label": {"type": "plain_text", "text": "What is the annual revenue?"},
            "element": {
                "type": "number_input",
                "action_id": "annual_revenue",
                **(
                    {"initial_value": initial_value_number("annual_revenue")}
                    if "annual_revenue" in deal_data
                    and deal_data.get("annual_revenue") is not None
                    else {}
                ),
                "is_decimal_allowed": False,
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter a number without commas or dollar signs!",
                },
            },
        },
        {
            "type": "input",
            "block_id": "profit_sde_ebitda",
            "label": {
                "type": "plain_text",
                "text": "What is the annual profit, SDE, EBITDA?",
            },
            "element": {
                "type": "number_input",
                "action_id": "profit_sde_ebitda",
                **(
                    {"initial_value": initial_value_number("what_is_the_annual_profit")}
                    if "what_is_the_annual_profit" in deal_data
                    and deal_data.get("what_is_the_annual_profit") is not None
                    else {}
                ),
                "is_decimal_allowed": False,
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter a number without commas or dollar signs!",
                },
            },
        },
        {
            "type": "input",
            "block_id": "operator_plan",
            "label": {
                "type": "plain_text",
                "text": "What is the plan for the operator?",
            },
            "element": {
                "type": "static_select",
                "action_id": "operator_plan",
                "placeholder": {"type": "plain_text", "text": "Select an option"},
                **(
                    {"initial_option": get_initial_option("plans_for_operator")}
                    if "plans_for_operator" in deal_data
                    and deal_data.get("plans_for_operator") is not None
                    else {}
                ),
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "I will operate PT and keep my job.",
                        },
                        "value": "I will operate PT and keep my job.",
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "I will operate FT and quit my job.",
                        },
                        "value": "I will operate FT and quit my job.",
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "I will operate for a short period of time and then hire an operator.",
                        },
                        "value": "I will operate for a short period of time and then hire an operator.",
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "I am immediately hiring an operator to run the company.",
                        },
                        "value": "I am immediately hiring an operator to run the company.",
                    },
                ],
            },
        },
        {
            "type": "input",
            "block_id": "employees",
            "label": {
                "type": "plain_text",
                "text": "How many employees are there?",
            },
            "element": {
                "type": "static_select",
                "action_id": "employees",
                "placeholder": {"type": "plain_text", "text": "Select an option"},
                **(
                    {
                        "initial_option": get_initial_option(
                            "how_many_employees_are_there_"
                        )
                    }
                    if "how_many_employees_are_there_" in deal_data
                    and deal_data.get("how_many_employees_are_there_") is not None
                    else {}
                ),
                "options": [
                    {
                        "text": {"type": "plain_text", "text": "None. Just the owner."},
                        "value": "None. Just the owner.",
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "1-5 Other than the owner",
                        },
                        "value": "1-5 Other than the owner",
                    },
                    {"text": {"type": "plain_text", "text": "6-10"}, "value": "6-10"},
                    {"text": {"type": "plain_text", "text": "10+"}, "value": "10+"},
                ],
            },
        },
        {
            "type": "input",
            "block_id": "deal_terms",
            "label": {
                "type": "plain_text",
                "text": "What are the basic terms of the deal structure?",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "deal_terms",
                "multiline": True,
                **(
                    {
                        "initial_value": get_initial_value(
                            "what_are_the_basic_terms_of_the_deal_structure___finances__payment_terms__transition_period__earn_o"
                        )
                    }
                    if "what_are_the_basic_terms_of_the_deal_structure___finances__payment_terms__transition_period__earn_o"
                    in deal_data
                    and deal_data.get(
                        "what_are_the_basic_terms_of_the_deal_structure___finances__payment_terms__transition_period__earn_o"
                    )
                    is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "finance_type",
            "label": {
                "type": "plain_text",
                "text": "Share how you financed the deal: ",
            },
            "element": {
                "type": "multi_static_select",
                "action_id": "finance_type",
                **(
                    {"initial_options": get_initial_options("financing_method")}
                    if "financing_method" in deal_data
                    and deal_data.get("financing_method") is not None
                    else {}
                ),
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select an option",
                },
                "options": [
                    {
                        "text": {"type": "plain_text", "text": "Cash"},
                        "value": "Cash",
                    },
                    {
                        "text": {"type": "plain_text", "text": "SBA Loan"},
                        "value": "SBA Loan",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Other Loan"},
                        "value": "Other Loan",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Seller Financing"},
                        "value": "Seller Financing",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Retirement Funds"},
                        "value": "Retirement Funds",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Heloc"},
                        "value": "Heloc",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Outside Capital"},
                        "value": "Outside Capital",
                    },
                    {
                        "text": {"type": "plain_text", "text": "Other"},
                        "value": "Other",
                    },
                ],
            },
        },
        {
            "type": "input",
            "block_id": "owner_details",
            "label": {"type": "plain_text", "text": "Owner Details"},
            "element": {
                "type": "plain_text_input",
                "action_id": "owner_details",
                **(
                    {"initial_value": get_initial_value("owner_details__if_any_")}
                    if "owner_details__if_any_" in deal_data
                    and deal_data.get("owner_details__if_any_") is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "own_cash",
            "label": {
                "type": "plain_text",
                "text": "How much of your own cash did you have to put into the deal?",
            },
            "element": {
                "is_decimal_allowed": False,
                "type": "number_input",
                "action_id": "own_cash",
                **(
                    {"initial_value": initial_value_number("cash_invested")}
                    if "cash_invested" in deal_data
                    and deal_data.get("cash_invested") is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "profit_expectations",
            "label": {
                "type": "plain_text",
                "text": "How much do you expect to put in your pocket annually (before growth) with debt service and any operator salaries considered?",
            },
            "element": {
                "is_decimal_allowed": False,
                "type": "number_input",
                "action_id": "profit_expectations",
                **(
                    {
                        "initial_value": initial_value_number(
                            "how_much_do_you_expect_to_be_able_to_out_in_your_own_pocket_annually__before_growth__with_debt_serv"
                        )
                    }
                    if "how_much_do_you_expect_to_be_able_to_out_in_your_own_pocket_annually__before_growth__with_debt_serv"
                    in deal_data
                    and deal_data.get(
                        "how_much_do_you_expect_to_be_able_to_out_in_your_own_pocket_annually__before_growth__with_debt_serv"
                    )
                    is not None
                    else {}
                ),
            },
        },
        {
            "type": "input",
            "block_id": "mailing_address",
            "label": {
                "type": "plain_text",
                "text": "What's your full mailing address so we can send you a special gift for your hard work!?",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "mailing_address",
            },
        },
        {
            "type": "input",
            "block_id": "file_input",
            "label": {
                "type": "plain_text",
                "text": "Please attach a copy of your purchase agreement.",
            },
            "element": {
                "type": "file_input",
                "action_id": "file_input",
                "filetypes": ["jpg", "png", "gif", "jpeg", "pdf"],
                "max_files": 1,
            },
        },
        {
            "type": "input",
            "dispatch_action": True,
            "block_id": "acquire_deal_before_or_after_joining",
            "label": {
                "type": "plain_text",
                "text": "Did you acquire the business before or after joining the Contrarian Community?",
            },
            "element": {
                "type": "radio_buttons",
                "action_id": "acquire_deal_before_or_after_joining",
                **(
                    {
                        "initial_option": get_initial_option(
                            "closed_before_or_after_joining_the_community"
                        )
                    }
                    if "closed_before_or_after_joining_the_community" in deal_data
                    and deal_data.get("closed_before_or_after_joining_the_community")
                    is not None
                    else {}
                ),
                "options": [
                    {
                        "text": {"type": "plain_text", "text": "before"},
                        "value": "before",
                    },
                    {"text": {"type": "plain_text", "text": "after"}, "value": "after"},
                ],
            },
        },
    ]

    guidant_checkbox_block = []
    secondary_payment_qs = []
    if pay_type in ["ROBS", "401(k)"]:
        guidant_checkbox_block = [
            {
                "type": "input",
                "block_id": "guidant_checkbox",
                "label": {
                    "type": "plain_text",
                    "text": "Did you use Guidant?",
                },
                "element": {
                    "type": "checkboxes",
                    "action_id": "guidant_checkbox",
                    **(
                        {"initial_options": get_initial_option("guidant_used")}
                        if "guidant_used" in deal_data
                        and deal_data.get("guidant_used") is not None
                        else {}
                    ),
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "Yes"},
                            "value": "true",
                        },
                        {
                            "text": {"type": "plain_text", "text": "No"},
                            "value": "false",
                        },
                    ],
                },
            }
        ]
    elif pay_type == "SBA Loan":
        secondary_payment_qs = [
            {
                "type": "input",
                "block_id": "sba_loan_lender",
                "label": {"type": "plain_text", "text": "Which lender did you use?"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "sba_loan_lender",
                    **(
                        {"initial_value": get_initial_value("sba_lender")}
                        if "sba_lender" in deal_data
                        and deal_data.get("sba_lender") is not None
                        else {}
                    ),
                },
            }
        ]

    acquired_after_blocks = []
    if acquire_deal_before_or_after_joining == "after":
        acquired_after_blocks = [
            {
                "type": "input",
                "block_id": "success_share_checkboxes",
                "optional": True,
                "label": {
                    "type": "plain_text",
                    "text": "We'd love to share your success with our audience. What, if anything, about this acquisition do you feel comfortable sharing?",
                },
                "element": {
                    "type": "checkboxes",
                    "action_id": "success_share_checkboxes",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Your Full Name",
                            },
                            "value": "Your Full Name",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Your First Name and Last Initial",
                            },
                            "value": "Your First Name and Last Initial",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Name of the company acquired",
                            },
                            "value": "Name of the company acquired",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Company's website",
                            },
                            "value": "Company's website",
                        },
                        {
                            "text": {"type": "plain_text", "text": "Purchase Price"},
                            "value": "Purchase price",
                        },
                        {
                            "text": {"type": "plain_text", "text": "Annual Revenue"},
                            "value": "Annual Revenue",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Annual Profit, SDE, EBITDA",
                            },
                            "value": "Annual Profit, SDE, EBITDA",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Basic terms of the deal",
                            },
                            "value": "Basic terms of the deal",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "How deal was financed",
                            },
                            "value": "How deal was financed",
                        },
                        {
                            "text": {"type": "plain_text", "text": "None of the above"},
                            "value": "None of the above",
                        },
                    ],
                },
            },
            {
                "type": "input",
                "block_id": "success_share_text",
                "label": {
                    "type": "plain_text",
                    "text": "If you'd like us to tag you on socials, please list your profile name(s) here!",
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "success_share_text",
                    **(
                        {
                            "initial_value": get_initial_value(
                                "if_you_d_like_us_to_tag_you_on_socials__please_list_your_profile_name_s__here_"
                            )
                        }
                        if "if_you_d_like_us_to_tag_you_on_socials__please_list_your_profile_name_s__here_"
                        in deal_data
                        and deal_data.get(
                            "if_you_d_like_us_to_tag_you_on_socials__please_list_your_profile_name_s__here_"
                        )
                        is not None
                        else {}
                    ),
                    "multiline": True,
                },
            },
        ]

    blocks = (
        header
        + inputfields
        + acquired_after_blocks
        + guidant_checkbox_block
        + secondary_payment_qs
    )
    private_metadata = json.dumps(current_state)
    try:
        response = slack_client.views_update(
            view_id=view_id,
            view={
                "type": "modal",
                "blocks": blocks,
                "close": {"type": "plain_text", "text": "Close"},
                "submit": {"type": "plain_text", "text": "Submit"},
                "title": {"type": "plain_text", "text": "Deal Closed"},
                "callback_id": "deal_closed_form_modal",
                "private_metadata": private_metadata,
            },
        )
    except Exception as e:
        logging.error(f"Failed to open loading modal: {e}")
        return None


def loading_modal(user_id, trigger_id):

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Loading...",
            },
        }
    ]

    response = slack_client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "blocks": blocks,
            "close": {"type": "plain_text", "text": "Close"},
            "title": {"type": "plain_text", "text": "Loading..."},
            "callback_id": "loading_modal",
        },
    )

    return response["view"]["id"]


def thank_you_modal(user_id, team_id, trigger_id, view_id):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Thanks! We've updated the deal in our system. If you entered any info incorrectly, please submit this form again and choose 'Update Existing Deal'.",
            },
        }
    ]

    response = slack_client.views_update(
        view_id=view_id,
        view={
            "type": "modal",
            "blocks": blocks,
            "close": {"type": "plain_text", "text": "Close"},
            "title": {"type": "plain_text", "text": "Thank you!"},
        },
    )
