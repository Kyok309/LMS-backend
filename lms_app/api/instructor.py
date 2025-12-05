import frappe

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_instructor_profile():
    instructor = frappe.get_value("Instructor_profile", "")