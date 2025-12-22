import frappe
from lms_app.utils.utils import response_maker
from lms_app.api.payment import check_payment_status

@frappe.whitelist(methods=["GET"])
def get_lessons():
    user = frappe.session.user
    if not frappe.db.exists("Has Role", {"parent": user, "role": "Student"}):
        response_maker(
            desc="Хичээлийн мэдээлэлд хандах эрхгүй байна.",
            status=403,
            type="error"
        )
        return
    course_id = frappe.request.args.get("courseId")
    print(course_id)
    if not check_payment_status(course_id, user):
        response_maker(
            desc="Төлбөр төлөгдөөгүй байна. Хичээлд хандах боломжгүй.",
            status=402,
            type="error"
        )
        return
    try:
        lessons = frappe.db.get_all(
            "Lesson",
            filters={"course": course_id},
            fields=["*"]
        )
        print(lessons)
        response_maker(
            desc="Хичээлийн мэдээллийг амжилттай авлаа.",
            data=lessons
        )
        return
    except:
        frappe.log(frappe.get_traceback(), "Get lessons error")
        print(frappe.get_traceback())
        response_maker(
            desc="Хичээлийн мэдээлэл авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return
    
@frappe.whitelist(methods=["GET"])
def get_lessons_instructor():
    user = frappe.session.user
    course_id = frappe.request.args.get("courseId")
    if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
        response_maker(
            desc="Хичээлийн мэдээлэлд хандах эрхгүй байна.",
            status=403,
            type="error"
        )
        return
    
    if not course_id:
        response_maker(
            desc="Сургалтын ID байхгүй байна.",
            status=400,
            type="error"
        )
        return
    
    if not frappe.db.exists("Course", course_id):
        response_maker(
            desc="Сургалт олдсонгүй.",
            status=404,
            type="error"
        )
        return
    try:
        instructor = frappe.get_value("Course", course_id, "instructor")
        
        if user == instructor:
            lessons = frappe.db.get_all(
                "Lesson",
                filters={"course": course_id},
                fields=["*"],
                order_by="order asc"
            )
            response_maker(
                desc="Хичээлийн мэдээллийг амжилттай авлаа.",
                data=lessons
            )
            return

        else:
            response_maker(
                desc="Хичээлийн мэдээлэлд хандах эрхгүй байна.",
                status=403,
                type="error"
            )
            return
    except Exception as e:
        frappe.log(frappe.get_traceback(), "Get courses instructor error")
        print(frappe.get_traceback())
        response_maker(
            desc="Хичээлийн мэдээлэл авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return

@frappe.whitelist(methods=["GET"])
def get_lesson():
    pass

@frappe.whitelist(methods=["GET"])
def get_lesson_instructor():
    user = frappe.session.user
    if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
        response_maker(
            desc="Хичээлийн мэдээлэлд хандах эрхгүй байна.",
            status=403,
            type="error"
        )
        return
    lesson_id = frappe.request.args.get("lessonId")
    if not lesson_id:
        response_maker(
            desc="Хичээлийн ID байхгүй байна.",
            status=404,
            type="error"
        )
        return
    
    lesson = frappe.get_doc("Lesson", lesson_id)
    if not lesson:
        response_maker(
            desc="Хичээл байхгүй байна.",
            status=404,
            type="error"
        )
        return
    try:
        lesson_contents = frappe.get_all("Lesson_content", filters={"lesson": lesson_id}, fields=["*"])
        
        response_maker(
            desc="Хичээлийн мэдээллийг амжилттай авлаа.",
            data=lesson
        )
    except:
        frappe.log_error(frappe.get_traceback, "Get lesson error")
        print(frappe.get_traceback)
        response_maker(
            desc="Хичээлийн мэдээлэл авахад алдаа гарлаа.",
            status=500,
            type="error"
        )

@frappe.whitelist(methods=["POST"])
def create_lesson():
    pass

@frappe.whitelist(methods=["PUT"])
def update_lesson():
    pass

@frappe.whitelist(methods=["PUT"])
def update_lessons_order():
    data = frappe.request.get_json() or {}
    lessons = {
        l["name"]: {"order": l["order"]} for l in data.get("lessons", [])
    }
    print(lessons)
    try:
        frappe.db.bulk_update(
            "Lesson",
            lessons,
            chunk_size = 200,
            update_modified = True
        )
        frappe.db.commit()
        response_maker(
            desc="Амжилттай өөрчлөгдлөө."
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Update lessons order error")
        print(frappe.get_traceback())
        response_maker(
            desc="Update lessons order error",
            status=500,
            type="error"
        )
        return

@frappe.whitelist(methods=["DELETE"])
def delete_lesson():
    pass
