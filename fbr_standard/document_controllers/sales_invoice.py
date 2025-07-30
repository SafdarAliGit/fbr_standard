import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice as SalesInvoiceController
from fbr_standard.api import FBRDigitalInvoicingAPI  
from frappe.utils import cint,flt
import pyqrcode



class SalesInvoice(SalesInvoiceController):
    def on_submit(self):
        super().on_submit()
        if not self.custom_post_to_fdi:
            return
        data = self.get_mapped_data()
        api_log = frappe.new_doc("FDI Request Log")
        api_log.request_data = frappe.as_json(data, indent=4)
        try:

            api = FBRDigitalInvoicingAPI()
            response = api.make_request("di_data/v1/di/postinvoicedata_sb", self.get_mapped_data())
            resdata = response.get("validationResponse")
            frappe.log_error(
                title="FBR Invoicing API Error",
                message=frappe.as_json(resdata, indent=4)
            )   
            
            # if resdata.get("status") == "Valid":
            #     self.custom_fbr_invoice_no = response.get("invoiceNumber")
            #     url = pyqrcode.create(self.custom_fbr_invoice_no)
            #     url.svg(frappe.get_site_path()+'/public/files/'+self.name+'_online_qrcode.svg', scale=8)
            #     self.custom_qr_code = '/files/'+self.name+'_online_qrcode.svg'
            #     api_log.response_data = frappe.as_json(response, indent=4)
            #     api_log.save()
            #     frappe.msgprint("Invoice successfully submitted to FBR Invoicing.")
            # else:
            #     api_log.response_data = frappe.as_json(response, indent=4)
            #     api_log.save()
            #     frappe.throw(
            #         "Error in FBR Invoicing" 
            #     )
                  
                
        except Exception as e:
            # api_log.error = frappe.as_json(e, indent=4)
            # api_log.save()
                
            # frappe.log_error(
            #     title="FBR Invoicing API Error",
            #     message=frappe.get_traceback()
            # )
            
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
                "totalValues": round(flt(item.amount + item.custom_tax_amount), 2),
                "valueSalesExcludingST": round(flt(item.amount), 2),
                "fixedNotifiedValueOrRetailPrice": 0,
                "salesTaxApplicable": round(flt(item.custom_tax_amount), 2),
                "salesTaxWithheldAtSource": 0,
                "extraTax": "",
                "furtherTax": 0,
                "sroScheduleNo": "",
                "fedPayable": 0,
                "discount": 0,
                "saleType": "Goods at standard rate (default)",
                "sroItemSerialNo": ""
            }
            items.append(item_data)
        return items


