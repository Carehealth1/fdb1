import streamlit as st
import requests
import json
from typing import Dict, Any

# Configuration and Setup
st.set_page_config(page_title="FDB API Tester", layout="wide")

# Constants
BASE_URL = "https://api.fdbcloudconnector.com/CC/api/v1_3"

def make_api_request(endpoint: str, client_id: str, client_secret: str) -> Dict[str, Any]:
    """Make an API request to FDB"""
    headers = {
        "Authorization": f"SHAREDKEY {client_id}:{client_secret}",
        "Accept": "application/json"
    }
    
    url = f"{BASE_URL}/{endpoint}"
    if "?" not in endpoint:
        url += "?callSystemName=StreamlitTest"
    else:
        url += "&callSystemName=StreamlitTest"
        
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return {
            "status": "success",
            "data": response.json(),
            "status_code": response.status_code
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": str(e),
            "status_code": getattr(e.response, 'status_code', None)
        }

def main():
    st.title("FDB API Testing Tool")
    
    # Sidebar for credentials
    with st.sidebar:
        st.header("Credentials")
        client_id = st.text_input("Client ID", type="password")
        client_secret = st.text_input("Client Secret", type="password")
        
        st.header("Available APIs")
        api_option = st.radio(
            "Select API",
            ["Drug Search", "Drug Details", "Drug Interactions", "Dosing Information", "Contraindications"]
        )

    # Main content area
    if not client_id or not client_secret:
        st.warning("Please enter your FDB credentials in the sidebar.")
        return

    # API-specific UI elements
    if api_option == "Drug Search":
        st.subheader("Search for Drugs")
        search_term = st.text_input("Enter drug name to search")
        if st.button("Search") and search_term:
            endpoint = f"DispensableDrugs/search?searchText={search_term}"
            result = make_api_request(endpoint, client_id, client_secret)
            display_result(result)

    elif api_option == "Drug Details":
        st.subheader("Get Drug Details")
        drug_id = st.text_input("Enter Drug ID")
        if st.button("Get Details") and drug_id:
            endpoint = f"DispensableDrugs/{drug_id}"
            result = make_api_request(endpoint, client_id, client_secret)
            display_result(result)

    elif api_option == "Drug Interactions":
        st.subheader("Check Drug Interactions")
        drug_id = st.text_input("Enter Drug ID")
        if st.button("Check Interactions") and drug_id:
            endpoint = f"DispensableDrugs/{drug_id}/DrugInteractions"
            result = make_api_request(endpoint, client_id, client_secret)
            display_result(result)

    elif api_option == "Dosing Information":
        st.subheader("Get Dosing Information")
        drug_id = st.text_input("Enter Drug ID")
        if st.button("Get Dosing Info") and drug_id:
            endpoint = f"DispensableDrugs/{drug_id}/DoseRecords"
            result = make_api_request(endpoint, client_id, client_secret)
            display_result(result)

    elif api_option == "Contraindications":
        st.subheader("Check Contraindications")
        drug_id = st.text_input("Enter Drug ID")
        if st.button("Check Contraindications") and drug_id:
            endpoint = f"DispensableDrugs/{drug_id}/Contraindications"
            result = make_api_request(endpoint, client_id, client_secret)
            display_result(result)

def display_result(result: Dict[str, Any]):
    """Display API response in a formatted way"""
    if result["status"] == "success":
        st.success(f"Request successful! Status code: {result['status_code']}")
        
        # Create tabs for different views of the data
        tab1, tab2 = st.tabs(["Formatted View", "Raw JSON"])
        
        with tab1:
            st.json(result["data"])
        
        with tab2:
            st.code(json.dumps(result["data"], indent=2), language="json")
    else:
        st.error(f"Error: {result['message']}")
        if result["status_code"]:
            st.error(f"Status code: {result['status_code']}")

if __name__ == "__main__":
    main()
