import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice as SalesInvoiceController
from fbr_standard.api import FBRDigitalInvoicingAPI  
from frappe.utils import cint
import pyqrcode



class SalesInvoice(SalesInvoiceController):
    def on_submit(self):
        super().on_submit()
        if not self.custom_post_to_fdi:
            return
        data = self.get_mapped_data()
        # api_log = frappe.new_doc("FDI Request Log")
        # api_log.request_data = frappe.as_json(data, indent=4)
        try:

            api = FBRDigitalInvoicingAPI()
            response = api.make_request("di_data/v1/di/postinvoicedata_sb", self.get_mapped_data())
            resdata = response.get("validationResponse")
            
            if resdata.get("status") == "Valid":
                self.custom_fbr_invoice_no = response.get("invoiceNumber")
                url = pyqrcode.create(self.custom_fbr_invoice_no)
                url.svg(frappe.get_site_path()+'/public/files/'+self.name+'_online_qrcode.svg', scale=8)
                self.custom_qr_code = '/files/'+self.name+'_online_qrcode.svg'
                # api_log.response_data = frappe.as_json(response, indent=4)
                # api_log.save()
                frappe.msgprint("Invoice successfully submitted to FBR Invoicing.")
            else:
                # api_log.response_data = frappe.as_json(response, indent=4)
                # api_log.save()
                frappe.throw(
                    "Error in FBR Invoicing" 
                )
                  
                
        except Exception as e:
            # api_log.error = frappe.as_json(e, indent=4)
            # api_log.save()
                
            frappe.log_error(
                title="FBR Invoicing API Error",
                message=frappe.get_traceback()
            )
            
            frappe.throw(f"Error while submitting invoice to FBR: {str(e)}")

        # api_log.save()
    def get_mapped_data(self):
        
        data = {}
        data["invoiceType"] = "Sale Invoice"
        data["invoiceDate"] = self.posting_date
        
        data["sellerNTNCNIC"] = self.company_tax_id
        data["sellerBusinessName"] = self.company
        data["sellerProvince"] = frappe.db.get_value("Company", self.company, "custom_province") or "Sindh"  # Default to Sindh if not set
        # Uncomment the next line if you have a seller address field
        #data["sellerAddress"] = self.seller.get("address")
        
        
        data["buyerNTNCNIC"] = self.tax_id if self.tax_id else ""
        data["buyerBusinessName"] = self.customer_name
        data["buyerProvince"] = self.territory or "Sindh"
        #data["buyerAddress"] = self.buyer.get("address")
        data["buyerRegistrationType"] = "Unregistered" if not self.tax_id else "Registered"
        data["scenarioId"] = "SN002" if not self.tax_id else "SN001"  # Adjust based on your logic
       
        data["items"] = self.get_items()
        
        return data
    
    def get_items(self):
        items = []
        for item in self.items:
            item_data = {
                "hsCode": str(frappe.db.get_value("Item", item.item_code, "custom_hs_code")) or "8517.1890",
                "productDescription": item.description,
                "rate": f"{item.custom_tax_rate}%",
                "uoM": item.uom,
                "quantity": cint(item.qty),
                "totalValues": item.amount + item.custom_tax_amount,
                "valueSalesExcludingST": item.amount,
                "fixedNotifiedValueOrRetailPrice": 0,
                "salesTaxApplicable": round(item.custom_tax_amount, 2),
                "salesTaxWithheldAtSource": 0,
                "extraTax": "",
                "furtherTax": 0,
                "sroScheduleNo": "",
                "fedPayable": 0,
                "discount": 0,
                "saleType": "Goods",
                "sroItemSerialNo": ""
            }
            items.append(item_data)
        return items


# import frappe
# from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice as SalesInvoiceController
# from fbr_standard.api import FBRDigitalInvoicingAPI  
# from frappe.utils import cint, flt, get_files_path
# import pyqrcode
# import os

# class SalesInvoice(SalesInvoiceController):
#     def on_submit(self):
#         super().on_submit()
        
#         if not self.custom_post_to_fdi:
#             return
            
#         # Validate required fields before proceeding
#         self.validate_fdi_fields()
        
#         # api_log = frappe.new_doc("FDI Request Log")
#         # api_log.request_data = frappe.as_json(self.get_mapped_data(), indent=4)
        
#         try:
#             api = FBRDigitalInvoicingAPI()
#             response = api.make_request("di_data/v1/di/postinvoicedata_sb", self.get_mapped_data())
            
#             if not response or not isinstance(response, dict):
#                 frappe.throw("Invalid response received from FBR API")
                
#             resdata = response.get("validationResponse", {})
            
#             # if resdata.get("status") == "Valid":
#             #     self.handle_success_response(response, api_log)
#             # else:
#             #     self.handle_error_response(response, api_log)
                
#         except Exception as e:
#             self.handle_api_exception(e)
            
#     def validate_fdi_fields(self):
#         """Validate required fields for FBR integration"""
#         required_fields = {
#             "company_tax_id": "Company Tax ID is required for FBR submission",
#             "posting_date": "Posting Date is required",
#         }
        
#         for field, message in required_fields.items():
#             if not self.get(field):
#                 frappe.throw(message)
                
#         for item in self.items:
#             if not item.get("custom_tax_rate") or not item.get("custom_tax_amount"):
#                 frappe.throw(f"Tax information missing for item {item.item_code}")

#     def handle_success_response(self, response):
#         """Process successful API response"""
#         self.custom_fbr_invoice_no = response.get("invoiceNumber")
        
#         if not self.custom_fbr_invoice_no:
#             frappe.throw("FBR Invoice Number not received in response")
            
#         # Generate and save QR code
#         try:
#             qr_code_path = self.generate_qr_code()
#             self.custom_qr_code = qr_code_path
#             self.save()
            
#             # api_log.response_data = frappe.as_json(response, indent=4)
#             # api_log.status = "Success"
#             # api_log.insert()
            
#             frappe.msgprint("Invoice successfully submitted to FBR Invoicing")
#         except Exception as e:
#             frappe.log_error(
#                 title="FBR QR Code Generation Error",
#                 message=f"Error generating QR code: {str(e)}\n\n{frappe.get_traceback()}"
#             )
#             frappe.msgprint("Invoice submitted to FBR but QR code generation failed", alert=True)

#     # def handle_error_response(self, response):
#         """Process API error response"""
#         error_msg = response.get("validationResponse", {}).get("message", "Unknown error occurred")
#         # api_log.response_data = frappe.as_json(response, indent=4)
#         # api_log.status = "Failed"
#         # api_log.error = error_msg
#         # api_log.insert()
        
#         frappe.throw(
#             f"FBR Validation Error: {error_msg}",
#             title="FBR Submission Failed"
#         )

#     def handle_api_exception(self, exception):
#         """Handle API exceptions"""
#         error_msg = str(exception)
        
#         frappe.log_error(
#             title="FBR Invoicing API Error",
#             message=f"Error: {error_msg}\n\n{frappe.get_traceback()}"
#         )
        
#         frappe.throw(
#             f"Error while submitting invoice to FBR: {error_msg}",
#             title="FBR Submission Error"
#         )

#     def generate_qr_code(self):
#         """Generate QR code for FBR invoice number"""
#         if not self.custom_fbr_invoice_no:
#             return ""
            
#         try:
#             qr = pyqrcode.create(self.custom_fbr_invoice_no)
#             filename = f"{self.name}_online_qrcode.svg"
#             filepath = os.path.join(get_files_path(), filename)
            
#             qr.svg(filepath, scale=8)
#             return f'/files/{filename}'
#         except Exception:
#             return ""

#     def get_mapped_data(self):
#         """Prepare data for FBR API"""
#         company_details = frappe.get_cached_value(
#             "Company", 
#             self.company, 
#             ["custom_province", "custom_company_address"], 
#             as_dict=True
#         )
        
#         data = {
#             "invoiceType": "Sale Invoice",
#             "invoiceDate": self.posting_date,
#             "sellerNTNCNIC": self.company_tax_id,
#             "sellerBusinessName": self.company,
#             "sellerProvince": company_details.get("custom_province") or "Sindh",
#             "sellerAddress": company_details.get("custom_company_address") or "",
#             "buyerNTNCNIC": self.tax_id or "",
#             "buyerBusinessName": self.customer_name,
#             "buyerProvince": self.territory or "Sindh",
#             "buyerRegistrationType": "Unregistered" if not self.tax_id else "Registered",
#             "scenarioId": self.get_scenario_id(),
#             "items": self.get_items()
#         }
        
#         return data
    
#     def get_scenario_id(self):
#         """Determine the appropriate scenario ID"""
#         if not self.tax_id:
#             return "SN002"
        
#         # Add more complex logic here if needed
#         return "SN001"

#     def get_items(self):
#         """Prepare item data for FBR API"""
#         items = []
        
#         for item in self.items:
#             hs_code = frappe.db.get_value("Item", item.item_code, "custom_hs_code") or "8517.1890"
            
#             item_data = {
#                 "hsCode": str(hs_code),
#                 "productDescription": item.description or item.item_name,
#                 "rate": f"{flt(item.custom_tax_rate, 2)}%",
#                 "uoM": item.uom,
#                 "quantity": item.qty,
#                 "totalValues": flt(item.amount + item.custom_tax_amount, 2),
#                 "valueSalesExcludingST": flt(item.amount, 2),
#                 "fixedNotifiedValueOrRetailPrice": 0,
#                 "salesTaxApplicable": flt(item.custom_tax_amount, 2),
#                 "salesTaxWithheldAtSource": 0,
#                 "extraTax": "",
#                 "furtherTax": 0,
#                 "sroScheduleNo": "",
#                 "fedPayable": 0,
#                 "discount": 0,
#                 "saleType": "Goods",
#                 "sroItemSerialNo": ""
#             }
#             items.append(item_data)
            
#         return items