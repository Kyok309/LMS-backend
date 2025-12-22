import frappe
from lms_app.utils.utils import response_maker
@frappe.whitelist(methods=["GET"])
def get_enrollments_student():
    user = frappe.session.user

    try:
        enrollments = frappe.db.get_all(
            "Enrollment",
            filters={"student": user},
            fields=["course", "enrolled_on", "progress_percentage", "completion_status"]
        )
        enrollment_course_ids = [e["course"] for e in enrollments]
        courses = frappe.db.get_all(
            "Course",
            filters={"name": ["in", enrollment_course_ids]},
            fields=["name", "course_title", "description"]
        )

        courses_map = {c["name"]: c for c in courses}

        for enrollment in enrollments:
            course = courses_map.get(enrollment["course"])
            enrollment["course_title"] = course["course_title"] if course else None
            enrollment["course_description"] = course["description"] if course else None

        response_maker(
            desc="Бүртгэлүүдийг амжилттай авлаа.",
            data=enrollments
        )
        return
    except Exception as e:
        print(frappe.get_traceback())
        response_maker(
            desc=str(e),
            status=500,
            type="error"
        )
        return