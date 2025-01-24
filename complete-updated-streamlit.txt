import streamlit as st
import requests
import json
import urllib.parse
from typing import Dict, Any
from datetime import datetime

# Configuration and Setup
st.set_page_config(page_title="FDB API Testing Tool", layout="wide")

# Constants
BASE_URL = "https://api.fdbcloudconnector.com/CC/api/v1_4"

def make_api_request(endpoint: str, client_id: str, client_secret: str, params: dict = None) -> Dict[str, Any]:
    """Make an API request to FDB"""
    if params is None:
        params = {}
    
    # Ensure callSystemName is always present
    if 'callSystemName' not in params:
        params['callSystemName'] = 'StreamlitTest'
        
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
    
    # Build the URL
    url = f"{BASE_URL}/{endpoint}"
    if params:
        query_string = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        url = f"{url}{'&' if '?' in url else '?'}{query_string}"
    
    try:
        st.write("Making request to:", url)
        response = requests.get(url, headers=headers)
        
        # Log response details
        st.write(f"Response Status Code: {response.status_code}")
        st.write(f"Response Headers: {dict(response.headers)}")
        
        # Check for specific status codes
        if response.status_code == 404:
            return {
                "status": "no_results",
                "message": "No results found for the search term.",
                "status_code": 404
            }
        elif response.status_code == 401:
            return {
                "status": "error",
                "message": "Authentication failed. Please check your credentials.",
                "status_code": 401
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
        return error_detail

def display_result(result: Dict[str, Any]):
    """Display API response in a formatted way"""
    if result["status"] == "success":
        st.success(f"Request successful! Status code: {result['status_code']}")
        
        # Create tabs for different views of the data
        tab1, tab2, tab3 = st.tabs(["Formatted View", "Raw JSON", "Analysis"])
        
        with tab1:
            if isinstance(result.get("data"), dict):
                # Handle different response types
                if "Items" in result["data"]:
                    st.write(f"Total Results: {result['data'].get('TotalResultCount', 0)}")
                    for item in result["data"]["Items"]:
                        st.write("---")
                        # Display common fields if they exist
                        common_fields = [
                            ("Drug", "PrescribableDrugDesc"),
                            ("Generic", "DispensableGenericDesc"),
                            ("Category", "DefaultETCDesc"),
                            ("RxNorm ID", "RxNormID"),
                            ("Route", "RouteDesc"),
                            ("Dose Form", "DoseFormDesc")
                        ]
                        for label, field in common_fields:
                            if field in item:
                                st.write(f"{label}: {item[field]}")
                        
                        with st.expander("View Details"):
                            st.json(item)
                elif "RxNormConcepts" in result["data"]:
                    st.write("RxNorm Concepts:")
                    for concept in result["data"]["RxNormConcepts"]:
                        st.write("---")
                        st.write(f"RxNorm ID: {concept.get('RxNormID')}")
                        st.write(f"Name: {concept.get('RxNormName')}")
                        st.write(f"Type: {concept.get('RxNormType')}")
                else:
                    st.json(result["data"])
        
        with tab2:
            st.code(json.dumps(result["data"], indent=2), language="json")
            
        with tab3:
            st.write("Response Analysis:")
            if isinstance(result["data"], dict):
                st.write("Number of top-level keys:", len(result["data"]))
                st.write("Available fields:", list(result["data"].keys()))
                if "Items" in result["data"]:
                    st.write("Number of items:", len(result["data"]["Items"]))
                    if result["data"]["Items"]:
                        st.write("Fields in each item:", list(result["data"]["Items"][0].keys()))
            elif isinstance(result["data"], list):
                st.write("Number of items:", len(result["data"]))
                if result["data"]:
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
             "Dosing Information", "Contraindications", "RxNorm Concepts",
             "Interoperable Drug Links", "Routed Dose Form Drugs"]
        )

    # Main content area
    if not client_id or not client_secret:
        st.warning("Please enter your FDB credentials in the sidebar.")
        return

    # API-specific UI elements
    if api_option == "Drug Search":
        st.subheader("Search for Drugs")
        st.info("This tool uses FDB's API to search for drug information.")
        
        search_term = st.text_input("Enter drug name to search")
        
        with st.expander("Example Searches"):
            st.markdown("""
            Try these common drug names:
            - clopidogrel (as shown in documentation)
            - acetaminophen (Tylenol)
            - ibuprofen (Advil)
            - amoxicillin
            - lisinopril
            """)
        
        advanced_options = st.expander("Advanced Search Options")
        with advanced_options:
            search_type = st.selectbox(
                "Search Type",
                ["startswith", "contains", "equals"],
                index=0
            )
            
            limit = st.number_input("Results Limit", min_value=1, max_value=1000, value=100)
            offset = st.number_input("Results Offset", min_value=0, value=0)
        
        if st.button("Search") and search_term.strip():
            # Clean search parameters
            search_term = search_term.strip()
            
            # Build query parameters as shown in documentation
            params = {
                "callSystemName": "StreamlitTest",
                "callid": datetime.now().strftime("%Y%m%d%H%M%S"),
                "searchtext": search_term,
                "searchtype": search_type,
                "limit": str(limit),
                "offset": str(offset)
            }
            
            # Make request to PrescribableDrugs endpoint
            endpoint = "PrescribableDrugs"
            result = make_api_request(endpoint, client_id, client_secret, params)
            
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
            params = {
                "callSystemName": "StreamlitTest",
                "callid": datetime.now().strftime("%Y%m%d%H%M%S")
            }
            endpoint = f"PrescribableDrugs/{drug_id}"
            result = make_api_request(endpoint, client_id, client_secret, params)
            display_result(result)

    elif api_option == "Drug Interactions":
        st.subheader("Check Drug Interactions")
        drug_id = st.text_input("Enter Drug ID")
        if st.button("Check Interactions") and drug_id:
            params = {
                "callSystemName": "StreamlitTest",
                "callid": datetime.now().strftime("%Y%m%d%H%M%S")
            }
            endpoint = f"PrescribableDrugs/{drug_id}/Interactions"
            result = make_api_request(endpoint, client_id, client_secret, params)
            display_result(result)

    elif api_option == "Dosing Information":
        st.subheader("Get Dosing Information")
        concept_type = st.selectbox(
            "Select Concept Type",
            ["PrescribableDrugs", "DispensableGenerics", "PackagedDrugs"]
        )
        drug_id = st.text_input("Enter Drug ID")
        if st.button("Get Dosing Info") and drug_id:
            params = {
                "callSystemName": "StreamlitTest",
                "callid": datetime.now().strftime("%Y%m%d%H%M%S")
            }
            endpoint = f"{concept_type}/{drug_id}/DoseRecords"
            result = make_api_request(endpoint, client_id, client_secret, params)
            display_result(result)

    elif api_option == "Contraindications":
        st.subheader("Check Contraindications")
        drug_id = st.text_input("Enter Drug ID")
        if st.button("Check Contraindications") and drug_id:
            params = {
                "callSystemName": "StreamlitTest",
                "callid": datetime.now().strftime("%Y%m%d%H%M%S")
            }
            endpoint = f"PrescribableDrugs/{drug_id}/Contraindications"
            result = make_api_request(endpoint, client_id, client_secret, params)
            display_result(result)
            
    elif api_option == "RxNorm Concepts":
        st.subheader("Get RxNorm Concepts")
        concept_type = st.selectbox(
            "Select Concept Type",
            ["DispensableDrugs", "DispensableGenerics", "PackagedDrugs"]
        )
        drug_id = st.text_input("Enter Drug ID")
        if st.button("Get RxNorm Concepts") and drug_id:
            params = {
                "callSystemName": "StreamlitTest",
                "callid": datetime.now().strftime("%Y%m%d%H%M%S")
            }
            endpoint = f"{concept_type}/{drug_id}/RxNormConcepts"
            result = make_api_request(endpoint, client_id, client_secret, params)
            display_result(result)

    elif api_option == "Interoperable Drug Links":
        st.subheader("Get Interoperable Drug Links")
        classification_id = st.text_input("Enter Classification ID")
        
        col1, col2 = st.columns(2)
        with col1:
            classification_type = st.selectbox(
                "Classification Type",
                ["ETC", "USC", "AHFS"]
            )
        with col2:
            interoperable_type = st.selectbox(
                "Interoperable Type",
                ["RxNormSemanticClinicalDrug", "RxNormPreciseIngredient"]
            )
            
        if st.button("Get Drug Links") and classification_id:
            params = {
                "callSystemName": "StreamlitTest",
                "callid": datetime.now().strftime("%Y%m%d%H%M%S"),
                "classificationType": classification_type,
                "interoperableType": interoperable_type
            }
            endpoint = f"Classifications/{classification_id}/InteroperableDrugLinks"
            result = make_api_request(endpoint, client_id, client_secret, params)
            display_result(result)

    elif api_option == "Routed Dose Form Drugs":
        st.subheader("Get Routed Dose Form Drugs")
        
        with st.expander("Search Options"):
            search_term = st.text_input("Search Term (optional)")
            limit = st.number_input("Results Limit", min_value=1, max_value=1000, value=100)
            offset = st.number_input("Results Offset", min_value=0, value=0)
        
        if st.button("Get Drugs"):
            params = {
                "callSystemName": "StreamlitTest",
                "callid": datetime.now().strftime("%Y%m%d%H%M%S"),
                "limit": str(limit),
                "offset": str(offset)
            }
            
            if search_term:
                params["searchText"] = search_term
                
            endpoint = "RoutedDoseFormDrugs"
            result = make_api_request(endpoint, client_id, client_secret, params)
            display_result(result)

if __name__ == "__main__":
    main()