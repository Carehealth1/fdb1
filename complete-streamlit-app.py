import streamlit as st
import requests
import json
import urllib.parse
from typing import Dict, Any
from datetime import datetime

# Configuration and Setup
st.set_page_config(page_title="FDB API Tester", layout="wide")

# Constants
BASE_URL = "https://api.fdbcloudconnector.com/CC/api/v1_3"

def make_api_request(endpoint: str, client_id: str, client_secret: str) -> Dict[str, Any]:
    """Make an API request to FDB"""
    # Debug information
    st.write("Request Details:")
    st.write(f"Endpoint: {BASE_URL}/{endpoint}")
    
    headers = {
        "Authorization": f"SHAREDKEY {client_id}:{client_secret}",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache"
    }
    
    # Debug headers (hide sensitive info)
    debug_headers = headers.copy()
    debug_headers["Authorization"] = "SHAREDKEY [HIDDEN]"
    st.write("Headers:", debug_headers)
    
    # Build the URL with proper encoding
    base_url = f"{BASE_URL}/{endpoint}"
    params = {
        "callSystemName": "StreamlitTest"
    }
    
    try:
        st.write("Making request to:", base_url)
        response = requests.get(
            base_url,
            headers=headers,
            params=params
        )
        
        # Log response details
        st.write(f"Response Status Code: {response.status_code}")
        st.write(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 404:
            st.warning(f"No results found for the search term. Try a different search term.")
            return {
                "status": "no_results",
                "data": {},
                "status_code": 404
            }
        
        response.raise_for_status()
        return {
            "status": "success",
            "data": response.json(),
            "status_code": response.status_code
        }
    except requests.exceptions.RequestException as e:
        error_detail = {
            "status": "error",
            "message": str(e),
            "status_code": getattr(e.response, 'status_code', None),
            "error_response": getattr(e.response, 'text', None)
        }
        st.error(f"Full error details: {json.dumps(error_detail, indent=2)}")
        return error_detail

def display_result(result: Dict[str, Any]):
    """Display API response in a formatted way"""
    if result["status"] == "success":
        st.success(f"Request successful! Status code: {result['status_code']}")
        
        # Create tabs for different views of the data
        tab1, tab2, tab3 = st.tabs(["Formatted View", "Raw JSON", "Response Analysis"])
        
        with tab1:
            st.json(result["data"])
        
        with tab2:
            st.code(json.dumps(result["data"], indent=2), language="json")
            
        with tab3:
            st.write("Response Analysis:")
            if isinstance(result["data"], dict):
                st.write("Number of top-level keys:", len(result["data"]))
                st.write("Available fields:", list(result["data"].keys()))
            elif isinstance(result["data"], list):
                st.write("Number of items:", len(result["data"]))
                if len(result["data"]) > 0 and isinstance(result["data"][0], dict):
                    st.write("Fields in first item:", list(result["data"][0].keys()))
    else:
        st.error(f"Error: {result['message']}")
        if result.get("error_response"):
            st.error("Error Response:")
            try:
                error_json = json.loads(result["error_response"])
                st.json(error_json)
            except json.JSONDecodeError:
                st.code(result["error_response"])
        if result["status_code"]:
            st.error(f"Status code: {result['status_code']}")

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
            ["Drug Search", "Drug Details", "Drug Interactions", 
             "Dosing Information", "Contraindications"]
        )

    # Main content area
    if not client_id or not client_secret:
        st.warning("Please enter your FDB credentials in the sidebar.")
        return

    # API-specific UI elements
    if api_option == "Drug Search":
        st.subheader("Search for Drugs")
        search_term = st.text_input("Enter drug name to search")
        
        with st.expander("Example Searches"):
            st.markdown("""
            Try these common drug names:
            - acetaminophen (Tylenol)
            - ibuprofen (Advil)
            - amoxicillin
            - lisinopril
            - metformin
            
            For chemotherapy drugs:
            - paclitaxel
            - doxorubicin
            - cyclophosphamide
            - trastuzumab
            """)
        
        advanced_options = st.expander("Advanced Search Options")
        
        with advanced_options:
            search_type = st.selectbox(
                "Search In",
                ["DispensableDrugs", "DispensableGenerics", "PackagedDrugs"]
            )
        
        if st.button("Search") and search_term.strip():
            # Clean and encode the search term
            search_term = search_term.strip().lower()
            search_term = urllib.parse.quote(search_term)
            
            # Build the endpoint
            endpoint = f"{search_type}/Search"
            params = {
                "searchText": search_term,
                "searchType": "Contains"
            }
            
            # Add params to endpoint
            endpoint += "?" + "&".join(f"{k}={v}" for k, v in params.items())
            
            result = make_api_request(endpoint, client_id, client_secret)
            
            if result["status"] == "no_results":
                st.warning("No results found. Try:")
                st.write("- Checking the spelling")
                st.write("- Using a different search term")
                st.write("- Trying a more common drug name")
            else:
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

if __name__ == "__main__":
    main()