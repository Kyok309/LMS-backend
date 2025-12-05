import frappe
from lms_app.utils.utils import response_maker

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_categories():
    try:
        categories = frappe.db.get_list("Category", filters={'is_active': 1}, fields=["name", "category_name"])
        response_maker(
            desc="Successfully fetched categories.",
            data=categories
        )
        return
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Categories Error")
        response_maker(
            desc="Алдаа гарлаа.",
            type="error"
        )
        return