import frappe
from lms_app.utils.utils import response_maker

def check_enrollment(student, course_id):
    return frappe.db.exists("Enrollment", {"student": student, "course": course_id})

@frappe.whitelist(methods=["GET"])
def check_enrollment_api(courseId):
    user = frappe.session.user
    print(user, courseId)
    if check_enrollment(user, courseId):
        response_maker(
            desc="Хэрэглэгч уг сургалтанд элссэн байна.",
            data={"enrolled": True}
        )
    else:
        response_maker(
            desc="Хэрэглэгч уг сургалтанд элсээгүй байна.",
            data={"enrolled": False}
        )
    return

@frappe.whitelist(methods=["GET"])
def get_enrollments_student():
    user = frappe.session.user
    try:
        enrollments = frappe.db.get_all(
            "Enrollment",
            filters={"student": user},
            fields=["course", "creation", "progress_percentage", "completion_status", "average_score", "completed_lessons"]
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
    
@frappe.whitelist(methods=["POST"])
def create_enrollment():
    user = frappe.session.user
    if not frappe.db.exists("Has Role", {"parent": user, "role": "Student"}):
        response_maker(
            desc="Суралцагчийн эрхээр нэвтэрнэ үү.",
            status=403,
            type="error"
        )
    try:
        course_id = frappe.request.args.get("courseId")
        if frappe.db.exists("Enrollment", {"student": user, "course": course_id}):
            response_maker(
                desc="Та уг сургалтанд аль хэдийн элссэн байна.",
                status=400,
                type="error"
            )
            return
        course = frappe.get_doc("Course", course_id)
        if course.price == 0:
            enrollment = frappe.get_doc({
                "doctype": "Enrollment",
                "course": course_id,
                "student": user
            })
            enrollment.insert()
            response_maker(
                desc="Сургалтанд амжилттай элслээ.",
            )
            return
        return
    except frappe.DoesNotExistError:
        response_maker(
            desc="Сургалт байхгүй байна.",
            status=404,
            type="error"
        )
        return
    except:
        frappe.log_error(frappe.get_traceback, "Create enrollment error")
        print(frappe.get_traceback())
        response_maker(
            desc="Сургалтанд элсэхэд алдаа гарлаа.",
            status=500,
            type="error"
        )
        return
        
