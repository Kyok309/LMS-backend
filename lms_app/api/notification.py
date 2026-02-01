import frappe
from lms_app.utils.utils import response_maker

@frappe.whitelist(methods=["GET"])
def get_notifications():
   try:
      user = frappe.session.user
      notifications = frappe.get_all("Notification Log",
         filters={"for_user": user},
         fields=["name", "subject", "email_content", "type", "read", "creation"],
         order_by = "creation desc"
      )
      response_maker(
         desc="Мэдэгдэл амжилттай авлаа.",
         data=notifications
      )
   except:
      frappe.log_error(frappe.get_traceback(), "Get notifications error")
      print(frappe.get_traceback())
      response_maker(
         desc="Мэдэгдэл авахад алдаа гарлаа.",
         status=500,
         type="error"
      )

@frappe.whitelist(methods=["PUT"])
def read_notification(notifId = None):
   if not notifId:
      response_maker(
         desc="Мэдэгдлийн ID байхгүй байна.",
         status=400,
         type="error"
      )
   user = frappe.session.user
   try:
      notification = frappe.get_doc("Notification Log", notifId)
      if notification.for_user == user:
         notification.update({
            "read": 1
         })
         notification.save()
         response_maker(
            desc="Мэдэгдэл амжилттай засагдлаа.",
         )
      else:
         response_maker(
            desc="Мэдэгдэл засах эрхгүй хэрэглэгч байна.",
            status=403,
            type="eror"
         )
   except:
      frappe.log_error(frappe.get_traceback(), "Read notification error")
      print(frappe.get_traceback())
      response_maker(
         desc="Мэдэгдэл засахад алдаа гарлаа.",
         status=500,
         type="error"
      )