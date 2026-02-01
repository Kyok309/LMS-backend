import frappe
from lms_app.utils.utils import response_maker
from frappe.model.workflow import apply_workflow

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_courses():
    try:
        categories = frappe.request.args.get("categories")
        min_price = frappe.request.args.get("min_price", 0, type=int)
        max_price = frappe.request.args.get("max_price", 1000000, type=int)
        sort_by = frappe.request.args.get("sort_by", "creation_desc")
        page = frappe.request.args.get("page", 1, type=int)
        search_query = frappe.request.args.get("search", "")
        level = frappe.request.args.get("level", "")
        
        category_list = [c.strip() for c in categories.split(",")] if categories else []
        
        field, direction = sort_by.rsplit("_", 1)
        order_by = f"{field} {direction}"
        
        filters = {"status": "Published", "price": ["between", [min_price, max_price]], "workflow_state": "Approved"}
        if level and level != "All":
            filters["level"] = level
            print(level)
        
        if category_list:
            filters["category"] = ["in", category_list]
        
        query = "%{}%".format(search_query.lower())

        instructor_ids = frappe.db.get_all(
            "User",
            or_filters=[
                ["User", "first_name", "like", query],
                ["User", "last_name", "like", query]
            ],
            pluck="name"
        )

        per_page = 9
        offset = (page - 1) * per_page
        
        filtered_courses = frappe.db.get_all(
            "Course",
            filters=filters,
            fields=["name", "course_title", "category", "instructor", "description", "introduction", "learning_curve", "requirement", "thumbnail", "price_type", "price", "level", "published_on", "creation"],
            order_by=order_by,
            or_filters=[
                ["Course", "course_title", "like", query],
                ["Course", "description", "like", query],
                ["Course", "instructor", "in", instructor_ids]
            ],
            start=offset,
            page_length=per_page
        )

        filtered_courses_instructor_ids = [c["instructor"] for c in filtered_courses]
        instructors = frappe.db.get_all(
            "User",
            filters={"name": ["in", filtered_courses_instructor_ids]},
            fields=["name", "full_name", "user_image"]
        )
        instructors_map = {i["name"]: i for i in instructors}

        filtered_courses_category_ids = [c["category"] for c in filtered_courses]
        categories = frappe.db.get_all(
            "Category",
            filters={"name": ["in", filtered_courses_category_ids]},
            fields=["name", "category_name"]
        )
        categories_map = {cat["name"]: cat for cat in categories}
        
        courses = []
        
        for course in filtered_courses:
            instructor_id = course.get("instructor")
            if instructor_id:
                full_name, user_image = instructors_map.get(instructor_id, {}).get("full_name"), instructors_map.get(instructor_id, {}).get("user_image")
                course["instructor_full_name"] = full_name
                course["instructor_image"] = user_image
            else:
                course["instructor_full_name"] = None
                course["instructor_image"] = None
            
            category_id = course.get("category")
            if category_id:
                category_name = categories_map.get(category_id, {}).get("category_name")
                course["category_name"] = category_name
            else:
                course["category_name"] = None

            student_count = frappe.db.count("Enrollment", {"course": course.get("name")})
            course["student_count"] = student_count
            lesson_count = frappe.db.count("Lesson", {"course": course.get("name")})
            course["lesson_count"] = lesson_count
            
            courses.append(course)
        
        total_count = len(frappe.db.get_list(
            "Course",
            filters=filters,
            or_filters=[
                ["Course", "course_title", "like", query],
                ["Course", "description", "like", query],
                ["Course", "instructor", "in", instructor_ids]
            ],
            fields=["name"]
        ))
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        response_maker(
            desc="Амжилттай",
            data={
                "courses": courses,
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages
            }
        )
        return
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get courses error")
        response_maker(
            desc="Сургалтын мэдээлэл авахад алдаа гарлаа.",
            type="error",
            status=500
        )
        print(frappe.get_traceback())
        return

@frappe.whitelist(methods=["GET"])
def get_courses_instructor():
    try:
        user = frappe.session.user
        if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
            response_maker(
                desc="Сургалтын мэдээлэлд хандах эрхгүй байна.",
                status=403,
                type="error",
            )
            return
        level = frappe.request.args.get("level")
        category = frappe.request.args.get("category")
        sort_by = frappe.request.args.get("sort_by", "creation_desc")
        search_query = frappe.request.args.get("search", "")
        page = frappe.request.args.get("page", 1, type=int)
        status = frappe.request.args.get("status", "All")

        filters={"instructor": user}

        if level and level != "All":
            filters["level"] = level
        if category and category != "All":
            filters["category"] = category
        if status and status != "All":
            filters["status"] = status

        field, direction = sort_by.rsplit("_", 1)
        order_by = f"{field} {direction}"

        query = "%{}%".format(search_query)

        per_page = 8
        offset = (page - 1) * per_page

        filtered_courses = frappe.db.get_all(
            "Course",
            filters=filters,
            fields="*",
            or_filters=[
                ["Course", "course_title", "like", query],
                ["Course", "description", "like", query]
            ],
            order_by=order_by,
            start=offset,
            page_length=per_page
        )
        
        filtered_courses_category_ids = [c["category"] for c in filtered_courses]
        categories = frappe.db.get_all(
            "Category",
            filters={"name": ["in", filtered_courses_category_ids]},
            fields=["name", "category_name"]
        )
        categories_map = {cat["name"]: cat for cat in categories}

        courses = []

        for course in filtered_courses:
            category_id = course.get("category")
            if category_id:
                course["category_name"] = categories_map.get(category_id, {}).get("category_name")
            else:
                course["category_name"] = None

            student_count = frappe.db.count("Enrollment", {"course": course.get("name")})
            course["student_count"] = student_count

            lesson_count = frappe.db.count("Lesson", {"course": course.get("name")})
            course["lesson_count"] = lesson_count

            courses.append(course)

        
        total_count = len(frappe.db.get_list(
            "Course",
            filters=filters,
            or_filters=[
                ["Course", "course_title", "like", query],
                ["Course", "description", "like", query]
            ],
            fields=["name"]
        ))
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

        response_maker(
            desc="Амжилттай",
            data={
                "courses": courses,
                "total_count": total_count,
                "total_pages": total_pages,
                "page": page
            }
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get courses error")
        print(frappe.get_traceback())
        response_maker(
            desc="Сургалтын мэдээлэл авахад алдаа гарлаа.",
            type="error",
            status=500
        )
        return
    
@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_course():
    try:
        courseId = frappe.form_dict.get("courseId")
        course = frappe.get_value(
            "Course", courseId,
            ["name", "course_title", "category", "instructor", "description", "introduction", "learning_curve", "requirement", "thumbnail", "price_type", "price", "level", "rating", "published_on", "creation"],
            as_dict=1
        )
        
        instructor_full_name, instructor_image = frappe.get_value("User", course["instructor"], ["full_name", "user_image"])
        if frappe.session.user:
            is_enrolled = frappe.db.exists("Enrollment", {"course": courseId, "student": frappe.session.user})
        else:
            is_enrolled = False
        data = course
        data["instructor_name"] = instructor_full_name
        data["instructor_image"] = instructor_image
        data["category_name"] = frappe.get_value("Category", course["category"], "category_name")
        data["total_students"] = frappe.db.count("Enrollment", {"course": course["name"]})
        data["is_enrolled"] = bool(is_enrolled)
        response_maker(
            desc="Амжилттай",
            data = data
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get courses error")
        print(frappe.get_traceback())
        response_maker(
            desc="Сургалтын мэдээлэл авахад алдаа гарлаа.",
            type="error",
            status=500
        )
        return
    
@frappe.whitelist(methods=["GET"])
def get_course_instructor():
    try:
        user = frappe.session.user
        if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
            response_maker(
                desc="Сургалтын мэдээлэлд хандах эрхгүй байна.",
                status=403,
                type="error",
            )
            return
        id = frappe.form_dict.get("id")
        if not id:
            response_maker(
                desc="Сургалтын ID байхгүй байна.",
                status=400,
                type="error"
            )
        course = frappe.get_doc("Course", id)
        if not course:
            response_maker(
                desc="Сургалт олдсонгүй.",
                status=404,
                type="error"
            )
            return
        if user == course.instructor:
            data = course.as_dict()
            data["category_name"] = frappe.get_value("Category", course.category, "category_name")
            data["total_students"] = frappe.db.count("Enrollment", {"course": course.name})
            response_maker(
                desc="Амжилттай",
                data = data
            )
            return
        else:
            response_maker(
                desc="Сургалтын мэдээлэлд хандах эрхгүй байна.",
                type="error",
                status=403
            )
            return
    except:
        frappe.log_error(frappe.get_traceback(), "Get courses error")
        print(frappe.get_traceback())
        response_maker(
            desc="Сургалтын мэдээлэл авахад алдаа гарлаа.",
            type="error",
            status=500
        )
        return

@frappe.whitelist(methods=["POST"])
def create_course():
    try:
        user = frappe.session.user
        if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
            response_maker(
                desc="Сургалт бүртгэх эрхгүй байна.",
                status=403,
                type="error",
            )
            return
        
        data = frappe.request.get_json() or {}

        instructor = data.get("instructor")
        if not user == instructor:
            response_maker(
                desc="Сургалт бүртгэх эрхгүй байна.",
                status=403,
                type="error",
            )
            return
        
        course_title = data.get("course_title")
        category = data.get("category")
        level = data.get("level")
        thumbnail = data.get("thumbnail")
        description = data.get("description")
        introduction = data.get("introduction")
        learning_curve = data.get("learning_curve")
        requirement = data.get("requirement")
        price_type = data.get("price_type")
        price = data.get("price")

        if not all([course_title, category, instructor, price_type, level]):
            response_maker(
                desc="Бүх талбарыг бөглөнө үү.",
                status=400,
                type="error",
            )
            return
        
        existing_course = frappe.db.exists("Course", {"course_title": course_title})
        
        if existing_course:
            response_maker(
                desc="Ижил нэртэй сургалт бүртгэгдсэн байна.",
                status=409,
                type="error",
            )
            return

        course = frappe.get_doc({
            "doctype": "Course",
            "instructor": instructor,
            "course_title": course_title,
            "category": category,
            "level": level,
            "thumbnail": thumbnail,
            "description": description,
            "introduction": introduction,
            "learning_curve": learning_curve,
            "requirement": requirement,
            "price_type": price_type,
            "price": price,
            "workflow_state": "Pending"
        })
        course.flags.ignore_mandatory = True

        course.insert()

        response_maker(
            desc="Сургалт амжилттай бүртгэгдлээ.",
            status=201,
            data=course
        )
        return
    except:
        response_maker(
            desc="Сургалт бүртгэхэд алдаа гарлаа.",
            status=500,
            type="error",
        )
        frappe.log_error(frappe.get_traceback(), "Create Course Error")
        print(frappe.get_traceback())
        return
    
@frappe.whitelist(methods=["PUT"])
def update_course():
    try:
        data = frappe.request.get_json() or {}
        user = frappe.session.user

        if not data.get("courseId"):
            response_maker(
                desc="Сургалтын ID байхгүй байна.",
                status=400,
                type="error"
            )
            return
        course = frappe.get_doc("Course", data.get("courseId"))
        
        ALLOWED_FIELDS = {
            "course_title",
            "category",
            "level",
            "thumbnail",
            "description",
            "introduction",
            "learning_curve",
            "requirement",
            "price_type",
            "price",
            "status"
        }

        if user == course.instructor:
            if course.workflow_state == "Approved" and course.status == "Published":
                apply_workflow(course, "Review")
            update_data = {
                k: v for k, v in data.items()
                if k in ALLOWED_FIELDS
            }
            course.update(update_data)
            course.save()
            response_maker(
                desc="Амжилттай засагдлаа.",
                status=201
            )
            return
        else:
            response_maker(
                desc="Сургалт засах эрхгүй байна.",
                status=403,
                type="error"
            )
            return
    except frappe.DoesNotExistError:
        response_maker(
            desc="Сургалт олдсонгүй.",
            status=404,
            type="error"
        )
        return
    except:
        response_maker(
            desc="Сургалт засахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        frappe.log_error(frappe.get_traceback(), "Create Course Error")
        print(frappe.get_traceback())
        return


@frappe.whitelist(methods=["DELETE"])
def delete_course():
    user = frappe.session.user

    courseId = frappe.request.args.get("courseId")
    if not courseId:
        response_maker(
            desc="Сургалтын ID байхгүй байна.",
            status=400,
            type="error"
        )
        return
    if frappe.db.exists("Enrollment", {"course": courseId}):
        response_maker(
            desc="Сургалтанд суралцагчид бүртгэлтэй тул сургалт устгах боломжгүй байна.",
            status=400,
            type="error"
        )
        return
    try:
        course = frappe.get_doc("Course", courseId)
        course.delete()
        if course.instructor == user:
            response_maker(
                desc="Сургалт амжилттай устгагдлаа."
            )
            return
        else:
            response_maker(
                desc="Сургалт устгах эрхгүй байна.",
                status=403,
                type="error"
            )
            return
    except frappe.DoesNotExistError:
        response_maker(
            desc="Сургалт олдсонгүй.",
            status=404,
            type="error"
        )
        return
    except Exception as e:
        print(frappe.get_traceback())
        response_maker(
            desc="Сургалт устгахад алдаа гарлаа.",
            status=e.status_code,
            type="error"
        )
        return