import frappe
import requests



class FBRDigitalInvoicingAPI:
    def __init__(self):
        settings = frappe.get_doc("Fbr Standard Settings")
        self.base_url = settings.get("url")
        self.token = settings.get_password("token")

    def init_request(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)


    def make_request(self, endpint, data):
        self.init_request()
        request = self.session.post(f"{self.base_url}/{endpint}", json=data)
        if request.status_code != 200:
            
            frappe.log_error(
                title="FBR Standard API Error",
                message=f"Error in FBR Standard API: {request.text}"
            )
            frappe.throw(f"Error in FBR Standard API: {request.text}")
        return request.json()
    

