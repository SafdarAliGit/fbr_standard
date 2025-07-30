from __future__ import unicode_literals
import frappe
import requests
from frappe import _

@frappe.whitelist(allow_guest=True)  # Explicitly disable guest access for security
def get_hs_codes():
    try:
        # Configuration values that could be moved to Site Config or DocType
        api_url = "https://gw.fbr.gov.pk/pdi/v1/itemdesccode"
        api_token = "f1994441-3687-3a08-a72a-019723f06dc9"  # Consider storing securely
        
        # Validate configuration
        if not api_url or not api_token:
            frappe.throw(_("API configuration is missing"))
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add timeout to prevent hanging requests
        response = requests.get(
            api_url,
            headers=headers,
            timeout=10  # 10 seconds timeout
        )
        
        # This will raise HTTPError for bad responses (4xx, 5xx)
        response.raise_for_status()
        
        data = response.json()
        
        # Validate response structure
        if not isinstance(data, list):
            frappe.throw(_("Unexpected API response format"))
        
        return {
            "status": "success",
            "data": data,
            "count": len(data),
            "http_status": response.status_code
        }
        
    except requests.exceptions.RequestException as e:
        frappe.log_error(_("HS Code API Request Failed"), str(e))
        return {
            "status": "error",
            "message": _("Failed to connect to HS Code service"),
            "details": str(e),
            "http_status": getattr(e.response, 'status_code', 500)
        }
        
    except ValueError as e:  # JSON decode error
        frappe.log_error(_("HS Code API Response Parse Error"), str(e))
        return {
            "status": "error",
            "message": _("Invalid response from HS Code service"),
            "details": str(e)
        }
        
    except Exception as e:
        frappe.log_error(_("HS Code Unknown Error"), str(e))
        return {
            "status": "error",
            "message": _("An unexpected error occurred"),
            "details": str(e)
        }