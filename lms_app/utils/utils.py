import frappe
def response_maker(desc="success", status=200, type="ok", data=None, meta=None, code=None):
    try:
        frappe.response["desc"] = desc
        frappe.response["http_status_code"] = status
        frappe.response["responseCode"] = code
        frappe.response["responseType"] = type
        
        if data:
            frappe.response["data"] = data
        else:
            frappe.response["data"] = []
        return
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Response Maker Error")
        frappe.response["desc"] = "Response maker error"
        frappe.response["http_status_code"] = 500
        frappe.response["responseType"] = "error"
        
        frappe.response["data"] = e.with_traceback()
        return