import frappe

def custom_on_update(doc, method):
    account = frappe.get_doc("Account", "GST - CTPL")
    rate = float(account.tax_rate) or frappe.throw("Tax rate undefined on GST - CTPL")

    for item in doc.items:
        item.custom_tax_rate = rate
        item.custom_tax_amount = round(item.amount * (rate / 100), 2)


