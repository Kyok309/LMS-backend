import frappe
from lms_app.utils.utils import response_maker
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Sum, Avg, NullIf, IfNull

@frappe.whitelist(methods=["GET"])
def get_report_instructor():
   user = frappe.session.user
   if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
      response_maker(
         desc="Тайлангийн мэдээлэл авах эрхгүй хэрэглэгч байна.",
         status=403,
         type="error"
      )
      return
   try:
      Course = DocType("Course")
      Enrollment = DocType("Enrollment")
      Payment = DocType("Payment")
      report = (frappe.qb
         .from_(Course)
         .left_join(Enrollment)
         .on(Course.name == Enrollment.course)
         .left_join(Payment)
         .on(Course.name == Payment.course)
         .select(Course.course_title, Course.published_on, Course.status, Course.price_type, Course.price, Course.workflow_state, Count(Enrollment.name).as_("enrollments"), Sum(Payment.amount).as_("total_revenue"))
         .where(Course.instructor == user)
         .groupby(Course.course_title)
      ).run(as_dict=True)
      response_maker(
         desc="Тайлангийн мэдээлэл амжилттай авлаа.",
         data=report
      )
   except:
      frappe.log_error(frappe.get_traceback(), "Get report error")
      print(frappe.get_traceback())
      response_maker(
         desc="Тайлангийн мэдээлэл авахад алдаа гарлаа.",
         status=500,
         type="error"
      )