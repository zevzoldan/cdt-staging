import threading
from flask import Flask, jsonify, make_response, request
import json, os
from pprint import pprint
from slack_sdk import WebClient

from dotenv import load_dotenv

from helpers import get_user_name, slack__get_file_url
from hubspot_helper.create_new_record import (
    associate_deal_with_contact,
    create_closed_community_acquisition_record,
    create_new_contact_record,
    update_deal_stage,
)
from hubspot_helper.query import get_contact_id
from hubspot_helper.submission_processor import (
    helper__send_submission_data_to_slack,
    process_deal_review_submission,
)
from modals import deals_modal
from slack_helper import send_deal_review_message, send_slack_to_success_share_channel

load_dotenv()

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello! This app was created by <a href='https://linkedin.com/in/zevzoldan'>Zev Zoldan</a>."


@app.route("/cdt-deal-staging", methods=["POST"])
@app.route("/deals", methods=["POST"])
def deals():
    print("Deals received")

    # Use request.get_json() instead of request.json() to avoid 415 error
    data = request.values

    user_id = data.get("user_id")
    team_id = data.get("team_id")
    trigger_id = data.get("trigger_id")
    print(f"deals form opened by {user_id} in team {team_id}")
    deals_modal.open_deals_modal(user_id, team_id, trigger_id, view_id=None)

    return make_response("", 200)


@app.route("/external_data_seeker", methods=["POST"])
def external_data_seeker():

    data = request.values
    try:
        data = json.loads(data["payload"])
        user_id = data.get("user").get("id")
        team_id = data.get("team").get("id")
        block_id = data.get("block_id", None)
        value = data.get("value", None)

    except Exception as e:
        print(f"error in external data seeker: {e}")
        data = []

    if data == []:
        return make_response("", 200)

    if block_id == "deal_id":
        from hubspot_helper.query import get_hubspot_comm_acquisition_records

        records = get_hubspot_comm_acquisition_records(user_id)
        if records is None or len(records) == 0:
            return make_response("", 200)

        theoptions = []

        for record in records:
            clean_name = f"{record[1]} - {record[3]}"  # max 75 characters
            if len(clean_name) > 70:
                clean_name = f"{clean_name[:70]}..."
            theoptions.append(
                {
                    "text": {
                        "type": "plain_text",
                        "text": clean_name,
                    },
                    "value": f"{record[0]}|{record[2]}",
                },
            )

        theresponse = {"options": theoptions}
        return make_response(jsonify(theresponse), 200)
    return make_response("", 200)


@app.route("/activity", methods=["GET", "POST"])
def activity():
    body = request.get_json()
    bodytype = body["type"]

    if bodytype == "url_verification":
        challenge = body["challenge"]
        return challenge

    if bodytype == "event_callback":
        event_type = body["event"]["type"]
        if event_type == "app_home_opened":
            user_id = body["event"]["user"]
            import screens.app_home

            screens.app_home.show_app_home_opened(user_id)
            print(f"App home opened by {user_id}")

        return make_response("", 200)


@app.route("/button", methods=["GET", "POST"])
def button():
    data = json.loads(request.form["payload"])

    buttontype = data["type"]
    token = data["token"]

    print(f"button pressed: {buttontype}")

    if buttontype == "view_submission":

        user_id = data["user"]["id"]
        trigger_id = data["trigger_id"]
        view_id = data["view"]["id"]
        team_id = data["team"]["id"]

        callback_id = data["view"]["callback_id"]
        modal_callback = callback_id
        print(f"modal {modal_callback} submitted by {user_id} in team {team_id}")

        if modal_callback == "basic_deal_info_form":
            private_metadata = data["view"]["private_metadata"]

            if isinstance(private_metadata, str) and private_metadata:
                private_metadata = json.loads(
                    private_metadata
                )  # Convert JSON string to dictionary

            deal_id = private_metadata.get("deal_id", None)
            deal_stage = private_metadata.get("deal_stage", None)

            profit_sde_ebitda = data["view"]["state"]["values"]["profit_sde_ebitda"][
                "profit_sde_ebitda"
            ]["value"]

            annual_revenue = data["view"]["state"]["values"]["annual_revenue"][
                "annual_revenue"
            ]["value"]

            company_name = data["view"]["state"]["values"]["company_name"][
                "company_name"
            ]["value"]

            business_description = data["view"]["state"]["values"][
                "business_description"
            ]["business_description"]["value"]

            business_type = data["view"]["state"]["values"]["business_type"][
                "business_type"
            ]["selected_option"]["value"]
            datatosend = {
                "deal_stage": deal_stage,
                "business_type_industry": business_type,
                "deal_name___description": business_description,
                "annual_revenue": annual_revenue,
                "what_is_the_annual_profit": profit_sde_ebitda,
                "company_name": company_name,
                "user_id": user_id,
                "submitted_by": get_user_name(user_id).get("real_name"),
            }

            deal_id = update_deal_stage(deal_id, datatosend)
            helper__send_submission_data_to_slack(
                user_id, "basic_deal_info_form", datatosend
            )
            if deal_id:
                contact_id = get_contact_id(user_id)
                if contact_id is None:
                    contact_id = create_new_contact_record(user_id)
                if contact_id:
                    associate_deal_with_contact(deal_id, contact_id)

        if modal_callback == "deal_closed_form_modal":
            private_metadata = data["view"]["private_metadata"]

            if isinstance(private_metadata, str) and private_metadata:
                private_metadata = json.loads(
                    private_metadata
                )  # Convert JSON string to dictionary

            deal_id = private_metadata.get("deal_id", None)
            deal_stage = private_metadata.get("deal_stage", None)
            company_name = None
            if "company_name" in data["view"]["state"]["values"]:
                company_name = data["view"]["state"]["values"]["company_name"][
                    "company_name"
                ]["value"]
            source = data["view"]["state"]["values"]["source"]["source"]["value"]
            website = data["view"]["state"]["values"]["website"]["website"]["value"]
            date_closed = data["view"]["state"]["values"]["date_closed"]["date_closed"][
                "selected_date"
            ]
            purchase_price = data["view"]["state"]["values"]["purchase_price"][
                "purchase_price"
            ]["value"]
            annual_revenue = data["view"]["state"]["values"]["annual_revenue"][
                "annual_revenue"
            ]["value"]
            profit_sde_ebitda = data["view"]["state"]["values"]["profit_sde_ebitda"][
                "profit_sde_ebitda"
            ]["value"]
            operator_plan = data["view"]["state"]["values"]["operator_plan"][
                "operator_plan"
            ]["selected_option"]["value"]
            employees = data["view"]["state"]["values"]["employees"]["employees"][
                "selected_option"
            ]["value"]
            deal_terms = data["view"]["state"]["values"]["deal_terms"]["deal_terms"][
                "value"
            ]
            finance_type_options = []
            finance_type = data["view"]["state"]["values"]["finance_type"][
                "finance_type"
            ]["selected_options"]
            for option in finance_type:
                finance_type_options.append(option["value"])
            finance_type_options = ";".join(finance_type_options)
            own_cash = data["view"]["state"]["values"]["own_cash"]["own_cash"]["value"]
            profit_expectations = data["view"]["state"]["values"][
                "profit_expectations"
            ]["profit_expectations"]["value"]
            mailing_address = data["view"]["state"]["values"]["mailing_address"][
                "mailing_address"
            ]["value"]
            file_input = data["view"]["state"]["values"][f"file_input"][f"file_input"][
                "files"
            ]
            # loop through the files and get the url
            file_urls = []
            for file in file_input:
                try:
                    channel_id = "C08FPMQS8LE"
                    if os.environ["ENV"] == "DEV":
                        channel_id = "C089FAUHSR5"
                    file_url = slack__get_file_url(
                        file, channel_id=channel_id, slack_ts=None
                    )
                    file_urls.append(file_url)
                except Exception as e:
                    file_url = None
            file_url = ";".join(file_urls)
            acquire_deal_before_or_after_joining = data["view"]["state"]["values"][
                "acquire_deal_before_or_after_joining"
            ]["acquire_deal_before_or_after_joining"]["selected_option"]["value"]

            sba_loan_lender = None
            if "sba_loan_lender" in data["view"]["state"]["values"]:
                sba_loan_lender = data["view"]["state"]["values"]["sba_loan_lender"][
                    "sba_loan_lender"
                ]["value"]

            guidant_checkbox = "false"
            if "guidant_checkbox" in data["view"]["state"]["values"]:
                guidant_checkbox = data["view"]["state"]["values"]["guidant_checkbox"][
                    "guidant_checkbox"
                ]["selected_options"][0]["value"]

            success_share_checkboxes = []
            clean_list = []
            if "success_share_checkboxes" in data["view"]["state"]["values"]:
                clean_list = data["view"]["state"]["values"][
                    "success_share_checkboxes"
                ]["success_share_checkboxes"]["selected_options"]
                for item in clean_list:
                    success_share_checkboxes.append(item["value"])
                # make the list seperated by a ;
                success_share_checkboxes = ";".join(success_share_checkboxes)
            trigger_slack_post = False
            if success_share_checkboxes == []:
                trigger_slack_post = False
                success_share_checkboxes = ";None of the above"
            else:
                trigger_slack_post = True
            success_share_text = None
            if "success_share_text" in data["view"]["state"]["values"]:
                success_share_text = data["view"]["state"]["values"][
                    "success_share_text"
                ]["success_share_text"]["value"]

            datatosend = {
                "source": source,
                "website": website,
                "date_closed": date_closed,
                "purchase_price": purchase_price,
                "annual_revenue": annual_revenue,
                "profit_sde_ebitda": profit_sde_ebitda,
                "operator_plan": operator_plan,
                "employees": employees,
                "deal_terms": deal_terms,
                "financing_method": finance_type_options,
                "own_cash": own_cash,
                "profit_expectations": profit_expectations,
                "mailing_address": mailing_address,
                "file_url": file_url,
                "acquire_deal_before_or_after_joining": acquire_deal_before_or_after_joining,
                "sba_loan_lender": sba_loan_lender,
                "guidant_checkbox": guidant_checkbox,
                "submitted_by": user_id,
                "user_id": user_id,
                "deal_stage": deal_stage,
                "success_share_text": success_share_text,
            }

            if company_name is not None:
                datatosend["company_name"] = company_name
            if success_share_checkboxes != []:
                datatosend["success_share_checkboxes"] = success_share_checkboxes

            create_closed_community_acquisition_record(datatosend, deal_id)
            helper__send_submission_data_to_slack(
                user_id, "deal_closed_form", datatosend
            )
            if trigger_slack_post:
                listofitemstopost = []
                print("success_share_checkboxes >>>", success_share_checkboxes)

                # split the success_share_checkboxes by ;
                success_share_checkboxes = success_share_checkboxes.split(";")

                for each_item in success_share_checkboxes:
                    if each_item == "Your Full Name":
                        listofitemstopost.append(
                            {"Your Full Name": get_user_name(user_id).get("real_name")}
                        )
                    elif each_item == "Your First Name and Last Initial":
                        listofitemstopost.append(
                            {
                                "Your First Name and Last Initial": (
                                    get_user_name(user_id)
                                    .get("real_name")
                                    .split(" ")[0]
                                    + " "
                                    + get_user_name(user_id)
                                    .get("real_name")
                                    .split(" ")[-1][:1]
                                )
                            }
                        )
                    elif each_item == "Name of the company acquired":
                        listofitemstopost.append(
                            {"Name of the company acquired": company_name}
                        )
                    elif each_item == "Company's website":
                        listofitemstopost.append({"Company's website": website})
                    elif each_item == "Purchase price":
                        listofitemstopost.append(
                            {"Purchase Price": f"${str(float(purchase_price))}"}
                        )
                    elif each_item == "Annual Revenue":
                        listofitemstopost.append(
                            {"Annual Revenue": f"${str(float(annual_revenue))}"}
                        )
                    elif each_item == "Annual Profit, SDE, EBITDA":
                        listofitemstopost.append(
                            {"Annual Profit, SDE, EBITDA": profit_sde_ebitda}
                        )
                    elif each_item == "Basic terms of the deal":
                        listofitemstopost.append(
                            {"Basic terms of the deal": deal_terms}
                        )
                    elif each_item == "How deal was financed":
                        listofitemstopost.append(
                            {"How deal was financed": finance_type_options}
                        )
                send_slack_to_success_share_channel(user_id, listofitemstopost)

        if modal_callback == "deal_review_form":
            private_metadata = data["view"]["private_metadata"]
            deal_id = private_metadata.split("|")[0]
            deal_stage = private_metadata.split("|")[1]
            if deal_id is None or deal_id == "None":
                deal_id = None
            company_name = data["view"]["state"]["values"]["company_name"][
                "company_name"
            ]["value"]
            share_mnl = data["view"]["state"]["values"]["share_mnl"]["share_mnl"][
                "selected_option"
            ]["value"]
            business_type = data["view"]["state"]["values"]["business_type"][
                "business_type"
            ]["selected_option"]["value"]
            business_description = data["view"]["state"]["values"][
                "business_description"
            ]["business_description"]["value"]
            if "location" in data["view"]["state"]["values"]:
                location = data["view"]["state"]["values"]["location"]["location"][
                    "value"
                ]
            else:
                location = None
            earnings_type = data["view"]["state"]["values"]["earnings_type"][
                "earnings_type"
            ]["selected_option"]["value"]
            sde_ebitda_2024 = data["view"]["state"]["values"]["sde_ebitda_2024"][
                "sde_ebitda_2024"
            ]["value"]
            sde_ebitda_2023 = data["view"]["state"]["values"]["sde_ebitda_2023"][
                "sde_ebitda_2023"
            ]["value"]
            sde_ebitda_2022 = data["view"]["state"]["values"]["sde_ebitda_2022"][
                "sde_ebitda_2022"
            ]["value"]
            sde_ebitda_2021 = data["view"]["state"]["values"]["sde_ebitda_2021"][
                "sde_ebitda_2021"
            ]["value"]
            revenue_2024 = data["view"]["state"]["values"]["revenue_2024"][
                "revenue_2024"
            ]["value"]
            revenue_2023 = data["view"]["state"]["values"]["revenue_2023"][
                "revenue_2023"
            ]["value"]
            revenue_2022 = data["view"]["state"]["values"]["revenue_2022"][
                "revenue_2022"
            ]["value"]
            revenue_2021 = data["view"]["state"]["values"]["revenue_2021"][
                "revenue_2021"
            ]["value"]
            asking_price = data["view"]["state"]["values"]["asking_price"][
                "asking_price"
            ]["value"]
            purchase_price = data["view"]["state"]["values"]["purchase_price"][
                "purchase_price"
            ]["value"]
            finance_type_options = []
            finance_type = data["view"]["state"]["values"]["finance_type"][
                "finance_type"
            ]["selected_options"]
            for option in finance_type:
                finance_type_options.append(option["value"])
            finance_type_options = ";".join(finance_type_options)
            owner_details = data["view"]["state"]["values"]["owner_details"][
                "owner_details"
            ]["value"]
            real_estate_percentage = data["view"]["state"]["values"][
                "real_estate_percentage"
            ]["real_estate_percentage"]["value"]
            additional_notes = data["view"]["state"]["values"]["additional_notes"][
                "additional_notes"
            ]["value"]
            concerns_questions = data["view"]["state"]["values"]["concerns_questions"][
                "concerns_questions"
            ]["value"]

            file_urls = []

            file_input = data["view"]["state"]["values"][f"file_input"][f"file_input"][
                "files"
            ]
            for file in file_input:
                try:
                    file_urls.append(file)
                except Exception as e:
                    continue

            deal_calculator_ready = data["view"]["state"]["values"][
                "deal_calculator_ready"
            ]["deal_calculator_ready"]["selected_options"][0]["value"]
            deal_calculator_link = None
            if "deal_calculator_link" in data["view"]["state"]["values"]:
                deal_calculator_link = data["view"]["state"]["values"][
                    "deal_calculator_link"
                ]["deal_calculator_link"]["value"]
            sde_calculator_link = None
            if "sde_calculator_link" in data["view"]["state"]["values"]:
                sde_calculator_link = data["view"]["state"]["values"][
                    "sde_calculator_link"
                ]["sde_calculator_link"]["value"]
            deal_box_link = None
            if "deal_box_link" in data["view"]["state"]["values"]:
                deal_box_link = data["view"]["state"]["values"]["deal_box_link"][
                    "deal_box_link"
                ]["value"]

            datatosend = {
                "share_mnl": share_mnl,
                "business_type": business_type,
                "business_description": business_description,
                "location": location,
                "earnings_type": earnings_type,
                "sde_ebitda_2024": sde_ebitda_2024,
                "sde_ebitda_2023": sde_ebitda_2023,
                "sde_ebitda_2022": sde_ebitda_2022,
                "sde_ebitda_2021": sde_ebitda_2021,
                "revenue_2024": revenue_2024,
                "revenue_2023": revenue_2023,
                "revenue_2022": revenue_2022,
                "revenue_2021": revenue_2021,
                "asking_price": asking_price,
                "purchase_price": purchase_price,
                "financing_method": finance_type_options,
                "deal_stage": deal_stage,
                "owner_details": owner_details,
                "real_estate_percentage": real_estate_percentage,
                "additional_notes": additional_notes,
                "concerns_questions": concerns_questions,
                "deal_calculator_ready": deal_calculator_ready,
                "deal_calculator_link": deal_calculator_link,
                "sde_calculator_link": sde_calculator_link,
                "deal_box_link": deal_box_link,
                "submitted_by": user_id,
                "user_id": user_id,
                "company_name": company_name,
                "files_for_slack": file_urls,
            }

            try:
                thread = threading.Thread(
                    target=process_deal_review_submission,
                    args=(datatosend, deal_id),
                )
                thread.start()
                # Don't join the thread here to avoid blocking the response
                # thread.join()
            except Exception as e:
                print(f"Error starting thread for deal review submission: {e}")

            return make_response("", 200)

    if buttontype == "block_actions":
        button_type = data["actions"][0]["type"]
        print(button_type)

        if button_type == "button":
            button_clicked_value = data["actions"][0]["value"]
            pprint(
                {
                    "type": buttontype,
                    "user_id": data["user"]["id"],
                    "team_id": data["team"]["id"],
                    "button_type": button_type,
                    "button_clicked_value": button_clicked_value,
                }
            )
            trigger_id = data["trigger_id"]
            user_id = data["user"]["id"]
            team_id = data["team"]["id"]
            try:
                view_id = data["view"]["id"]
                hash_id = data["view"]["hash"]
            except Exception as e:
                view_id = None
                hash_id = None

            if button_clicked_value == "create_new_deal":
                view_id = deals_modal.loading_modal(user_id, trigger_id)
                deals_modal.new_deal_select_stage(
                    user_id,
                    team_id,
                    trigger_id,
                    view_id,
                )

            if "app_home_update_deal" in button_clicked_value:
                deal_id = button_clicked_value.split("|")[1]
                view_id = deals_modal.loading_modal(user_id, trigger_id)
                deals_modal.existing_deal_select_stage(
                    user_id, team_id, trigger_id, view_id, deal_id
                )

            if button_clicked_value == "update_existing_deal":
                print("!!!!!")
                view_id = deals_modal.loading_modal(user_id, trigger_id)
                deals_modal.existing_deal_select_stage(
                    user_id,
                    team_id,
                    trigger_id,
                    view_id,
                )

        if button_type == "static_select":

            action_id = data["actions"][0]["action_id"]
            trigger_id = data["trigger_id"]
            user_id = data["user"]["id"]
            team_id = data["team"]["id"]
            view_id = data["view"]["id"]

            selected_option = data["actions"][0]["selected_option"]["value"]

            print(
                f"static select button ({action_id}) clicked by {user_id} in team {team_id}: {selected_option}"
            )

            if "existing_deal_select_deal_stage" in action_id:
                print("Deal stage selected")
                deal_id = action_id.split("|")[1]

                # Convert private_metadata back to string if it's a dictionary
                private_metadata = {
                    "deal_id": deal_id,
                    "deal_type": "existing",
                }

                if selected_option in [
                    "Offer Not Made",
                    "Offer Not Accepted",
                    "Deal Didn't Close",
                ]:
                    import modals.deals_modal as dm

                    dm.thank_you_modal(user_id, team_id, trigger_id, view_id)
                    update_deal_stage(
                        deal_id,
                        {
                            "deal_stage": selected_option,
                            "user_id": user_id,
                            "submitted_by": get_user_name(user_id).get("real_name"),
                        },
                    )
                    helper__send_submission_data_to_slack(
                        user_id,
                        "update_deal_stage",
                        {
                            "deal_stage": selected_option,
                            "deal_id": deal_id,
                            "user_id": user_id,
                            "submitted_by": get_user_name(user_id).get("real_name"),
                        },
                    )

                if selected_option in [
                    "Closed - Won",
                    "Closed - Lost",
                    "Deal Closed",
                ]:
                    deals_modal.deal_closed_form_modal(
                        user_id,
                        team_id,
                        trigger_id,
                        view_id,
                        private_metadata,
                        "deal_stage",
                        selected_option,
                    )
                    return make_response("", 200)
                if selected_option in [
                    "NDA Signed",
                    "LOI Submitted",
                    "LOI Accepted",
                    "Purchase Agreement Submitted",
                    "Purchase Agreement Accepted",
                ]:
                    import modals.deals_modal as dm

                    dm.submit_a_deal_review(
                        user_id,
                        team_id,
                        trigger_id,
                        view_id,
                        deal_id=None,
                        input_data=private_metadata,
                        updated_field="deal_stage",
                        updated_value=selected_option,
                    )

                    return make_response("", 200)

            if action_id == "new_deal_select_stage":
                private_metadata = data["view"]["private_metadata"]
                import modals.deals_modal as dm

                # - NDA Signed [in progress]
                # - LOI Submitted [in progress]
                # - LOI Accepted [in progress]
                # - Purchase Agreement Submitted [in progress]
                # - Purchase Agreement Accepted [in progress]
                # - Offer Not Made [offer not made/not closed]
                # - Offer Not Accepted [offer not made/not closed]
                # - Deal Didn't Close [offer not made/not closed]
                # - Deal Closed
                print("we here bud")
                if selected_option in [
                    "NDA Signed",
                    "LOI Submitted",
                    "LOI Accepted",
                    "Purchase Agreement Submitted",
                    "Purchase Agreement Accepted",
                ]:
                    dm.submit_a_deal_review(
                        user_id,
                        team_id,
                        trigger_id,
                        view_id,
                        deal_id=None,
                        input_data=private_metadata,
                        updated_field="deal_stage",
                        updated_value=selected_option,
                    )
                    return make_response("", 200)

                if selected_option in [
                    "Offer Not Made",
                    "Offer Not Accepted",
                    "Deal Didn't Close",
                ]:
                    dm.basic_deal_info_form(
                        user_id,
                        team_id,
                        trigger_id,
                        view_id,
                        deal_id=None,
                        input_data=private_metadata,
                        updated_field="deal_stage",
                        updated_value=selected_option,
                    )
                    return make_response("", 200)

                if selected_option in [
                    "Closed - Won",
                    "Closed - Lost",
                    "Deal Closed",
                ]:
                    deals_modal.deal_closed_form_modal(
                        user_id,
                        team_id,
                        trigger_id,
                        view_id,
                        private_metadata,
                        "deal_stage",
                        selected_option,
                    )
                    return make_response("", 200)

                else:
                    deals_modal.deal_review_form_modal(
                        user_id, team_id, trigger_id, view_id, selected_option, None
                    )
                    return make_response("", 200)

            if "select_deal_id" in action_id:
                deal_id = selected_option

                deals_modal.existing_deal_select_stage(
                    user_id, team_id, trigger_id, view_id, deal_id
                )
            if "payment_method" in action_id:
                private_metadata = data["view"]["private_metadata"]
                print("Payment method selected", selected_option)

                if selected_option in ["SBA Loan", "ROBS", "401(k)"]:
                    deals_modal.deal_closed_form_modal(
                        user_id,
                        team_id,
                        trigger_id,
                        view_id,
                        private_metadata,
                        "pay_type",
                        selected_option,
                    )

        if button_type == "radio_buttons":

            print("Radio button clicked")
            private_metadata = data["view"]["private_metadata"]
            print("private_metadata", private_metadata)
            action_id = data["actions"][0]["action_id"]
            trigger_id = data["trigger_id"]
            user_id = data["user"]["id"]
            team_id = data["team"]["id"]
            view_id = data["view"]["id"]

            selected_option = data["actions"][0]["selected_option"]["value"]

            print(
                f"Radio button ({action_id}) clicked by {user_id} in team {team_id}: {selected_option}"
            )

            if "acquire_deal_before_or_after_joining" in action_id:
                if selected_option == "after":
                    private_metadata = data["view"]["private_metadata"]
                    deals_modal.deal_closed_form_modal(
                        user_id,
                        team_id,
                        trigger_id,
                        view_id,
                        private_metadata,
                        "acquire_deal_before_or_after_joining",
                        "after",
                    )

            if action_id == "submit_a_deal_review":
                private_metadata = data["view"]["private_metadata"]
                private_metadata = json.loads(private_metadata)
                deal_stage = private_metadata.get("deal_stage")
                if selected_option == "Yes":
                    if "deal_id" in private_metadata:
                        deal_stage = private_metadata.get("deal_stage")

                        deals_modal.deal_review_form_modal(
                            user_id,
                            team_id,
                            trigger_id,
                            view_id,
                            deal_stage,
                            private_metadata.get("deal_id"),
                        )
                    else:
                        deals_modal.deal_review_form_modal(
                            user_id, team_id, trigger_id, view_id, deal_stage, None
                        )

                if selected_option == "No":
                    import modals.deals_modal as dm

                    dm.basic_deal_info_form(
                        user_id, team_id, trigger_id, view_id, None, private_metadata
                    )

            if action_id == "deal_type":
                deal_type = data["actions"][0]["selected_option"]["value"]

                if deal_type == "reporting_new_deal":
                    deals_modal.new_deal_select_stage(
                        user_id, team_id, trigger_id, view_id
                    )

                    # deals_modal.deal_review_form_modal(
                    #     user_id, team_id, trigger_id, view_id
                    # )

                if deal_type == "updating_existing_deal":
                    deals_modal.existing_deal_select_stage(
                        user_id, team_id, trigger_id, view_id
                    )

    return make_response("", 200)


if __name__ == "__main__":
    if os.environ["ENV"] == "DEV":
        print("Running in DEV mode")

        app.run(port=3000, debug=True)

    ## To be used in Production only. Setup in Heroku > Settings > Variables. ##
    elif os.environ["ENV"] == "PROD":
        app.run(host="0.0.0.0")
