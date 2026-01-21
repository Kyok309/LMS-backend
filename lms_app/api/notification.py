import frappe
from lms_app.utils.utils import response_maker

@frappe.whitelist(methods=["GET"])
def get_notifications():
   user = frappe.session.user
   