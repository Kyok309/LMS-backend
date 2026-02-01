import frappe
from lms_app.utils.utils import response_maker
from lms_app.api.enrollment import check_enrollment
from frappe.query_builder import DocType

@frappe.whitelist(methods=["POST"])
def get_lesson_file(lesson_id, file_url):
    user = frappe.session.user
    # 1. Get lesson
    lesson = frappe.get_doc("Lesson", lesson_id)

    # 2. Check enrollment
    if not check_enrollment(user, lesson.course):
        response_maker(
            desc="Файлд хандах эрхгүй байна.",
            status=403,
            type="error"
        )

    # 3. Get file doc
    file = frappe.get_doc("File", {"file_url": file_url})

    # 4. Final permission safety
    if file.is_private != 1:
        frappe.throw("Invalid file access")

    # 5. Stream file
    frappe.local.response.filename = file.file_name
    frappe.local.response.filecontent = file.get_content()
    frappe.local.response.type = "download"


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
    if not check_enrollment(user, course_id):
        response_maker(
            desc="Уг сургалтанд элсээгүй байна.",
            status=403,
            type="error"
        )
        return
    try:
        Lesson_student = DocType("Lesson_student")
        Lesson = DocType("Lesson")
        Course = DocType("Course")
        lessons = (
            frappe.qb
            .from_(Lesson)
            .left_join(Lesson_student)
            .on((Lesson.name == Lesson_student.lesson) & (Lesson_student.student == user))
            .join(Course)
            .on(Lesson.course == Course.name)
            .select(
                Lesson.name, Lesson.lesson_title, Lesson.description, Lesson.order, Lesson_student.status
            )
            .where(
                Course.name == course_id
            )
            .orderby(Lesson.order)
        ).run(as_dict = True)
        course_title = frappe.get_value("Course", course_id, "course_title")
        print(lessons)
        response_maker(
            desc="Хичээлийн мэдээллийг амжилттай авлаа.",
            data={"lessons":lessons, "course_title": course_title}
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get lessons error")
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
                fields=["name", "lesson_title", "order"],
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
        
    except:
        frappe.log(frappe.get_traceback(), "Get courses instructor error")
        print(frappe.get_traceback())
        response_maker(
            desc="Хичээлийн мэдээлэл авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return

@frappe.whitelist(methods=["GET"])
def get_lesson(courseId=None, lessonId = None):
    user = frappe.session.user
    if not check_enrollment(user, courseId):
        response_maker(
            desc="Уг сургалтанд элсээгүй байна.",
            status=403,
            type="error"
        )
        return
    try:
        lesson = frappe.get_doc("Lesson", lessonId)
        lesson.lesson_content = sorted(
            lesson.lesson_content,
            key=lambda x: x.order or 0
        )
        course = frappe.get_value("Course", lesson.course, ["course_title", "instructor"], as_dict=1)
        instructor = frappe.get_value("User", course["instructor"], ["first_name", "last_name", "user_image"], as_dict=1)
        response_maker(
            desc="Хичээл амжилттай авлаа.",
            data={
                **lesson.as_dict(),
                **course,
                **instructor
            }
        )
        return
    except frappe.DoesNotExistError:
        response_maker(
            desc="Хичээл олдсонгүй.",
            status=404,
            type="error"
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get lesson error")
        print(frappe.get_traceback())
        response_maker(
            desc="Хичээлийн мэдээлэл авахад алдаа гарлаа.",
            status=500,
            type="error"
        )

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
        
    try:
        lesson = frappe.get_doc("Lesson", lesson_id)
        course_title = frappe.get_value("Course", lesson.course, "course_title")
        print(course_title)
        lesson_dict = lesson.as_dict()
        lesson_dict["course_title"] = course_title
        response_maker(
            desc="Хичээлийн мэдээллийг амжилттай авлаа.",
            data=lesson_dict
        )
        return
    except frappe.DoesNotExistError:
        response_maker(
            desc="Хичээл байхгүй байна.",
            status=404,
            type="error"
        )
        return
    except Exception:
        frappe.log_error(frappe.get_traceback, "Get lesson error")
        print(frappe.get_traceback)
        response_maker(
            desc="Хичээлийн мэдээлэл авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return

@frappe.whitelist(methods=["POST"])
def create_lesson(lesson_title=None, order=None, course=None, description = None, lesson_content = []):
    user = frappe.session.user
    if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
        response_maker(
            desc="Хичээл үүсгэх эрхгүй байна.",
            status=403,
            type="error"
        )
        return
    if not all([lesson_title, order, course]):
        response_maker(
            desc="Мэдээлэл дутуу байна.",
            status=400,
            type="error"
        )
        return
    try:
        lesson = frappe.get_doc({
            "doctype": "Lesson",
            "lesson_title": lesson_title,
            "description": description,
            "course": course,
            "order": order,
            "lesson_content": lesson_content
        })
        lesson.insert()

        response_maker(
            desc="Хичээлийг амжилттай хадгаллаа.",
            data=lesson
        )
        return

    except frappe.ValidationError as e:
        response_maker(
            desc=str(e),
            status=400,
            type="error"
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Create lesson error")
        print(frappe.get_traceback())
        response_maker(
            desc="Хичээл үүсгэхэд алдаа гарлаа.",
            status=500,
            type="error"
        )
        return

@frappe.whitelist(methods=["PUT"])
def update_lesson():
    try:
        user = frappe.session.user
        data = frappe.request.get_json() or {}
        ALLOWED_FIELDS = {
            "lesson_title",
            "description",
            "lesson_content"
        }
        lesson = frappe.get_doc("Lesson", data.get("name"))
        if user == frappe.get_value("Course", {"name": lesson.course}, "instructor"):
            update_data = {
                k: v for k, v in data.items()
                if k in ALLOWED_FIELDS
            }
            lesson.update(update_data)
            lesson.save()
            response_maker(
                desc="Амжилттай засагдлаа.",
                status=201
            )
            return

    except frappe.ValidationError as e:
        response_maker(
            desc=str(e),
            status=400,
            type="error"
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Update lesson error")
        print(frappe.get_traceback())
        response_maker(
            desc="Хичээлийн мэдээлэл засахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return

@frappe.whitelist(methods=["PUT"])
def update_lessons_order():
    data = frappe.request.get_json() or {}
    lessons = {
        l["name"]: {"order": l["order"]} for l in data.get("lessons", [])
    }
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
def delete_lesson(lessonId = None):
    try:
        user = frappe.session.user
        lesson = frappe.get_doc("Lesson", lessonId)
        instructor = frappe.get_value("Course", lesson.course, "instructor")
        print(instructor)
        if user == instructor:
            lesson.delete()
            response_maker(
                desc="Хичээл амжилттай устгагдлаа.",
            )
            return
        else:
            response_maker(
                desc="Хичээл устгах эрхгүй байна.",
                status=403,
                type="error"
            )
            return
    except frappe.DoesNotExistError:
        response_maker(
            desc="Хичээл олдсонгүй.",
            status=404,
            type="error"
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Delete lesson error")
        print(frappe.get_traceback())
        response_maker(
            desc="Хичээл устгахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return