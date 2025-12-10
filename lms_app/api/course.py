import frappe
from lms_app.utils.utils import response_maker

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
        
        filters = {"status": "Published", "price": ["between", [min_price, max_price]]}
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
            fields="*",
            order_by=order_by,
            or_filters=[
                ["Course", "course_title", "like", query],
                ["Course", "description", "like", query],
                ["Course", "instructor", "in", instructor_ids]
            ],
            start=offset,
            page_length=per_page
        )
        
        courses = []
        
        for course in filtered_courses:
            
            instructor_id = course.get("instructor")
            if instructor_id:
                full_name, user_image = frappe.get_value("User", instructor_id, ["full_name", "user_image"])
                course["instructor_full_name"] = full_name
                course["instructor_image"] = user_image
            else:
                course["instructor_full_name"] = None
                course["instructor_image"] = None
            
            category_id = course.get("category")
            if category_id:
                category_name = frappe.get_value("Category", category_id, "category_name")
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
        level = frappe.request.args.get("level")
        category = frappe.request.args.get("category")
        sort_by = frappe.request.args.get("sort_by", "creation_desc")
        search_query = frappe.request.args.get("search", "")
        page = frappe.request.args.get("page", 1, type=int)

        field, direction = sort_by.rsplit("_", 1)
        order_by = f"{field} {direction}"

        filters={"status": "Published", "instructor": user}
        if level and level != "All":
            filters["level"] = level
        if category and category != "All":
            filters["category"] = category

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
        
        courses = []

        for course in filtered_courses:
            category_id = course.get("category")
            if category_id:
                course["category_name"] = frappe.get_value("Category", category_id, "category_name")
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
        id = frappe.form_dict.get("id")
        print(id)
        course = frappe.get_doc("Course", id)
        instructor = frappe.get_doc("User", course.instructor)
        instructor_name = instructor.full_name
        instructor_image = instructor.user_image
        category = frappe.get_value("Category", course.category, "category_name")
        total_students = frappe.db.count("Enrollment", {"course": course.name})
        print(course)
        print(instructor)
        print(category)
        data = course.as_dict()
        data["instructor_name"] = instructor_name
        data["instructor_image"] = instructor_image
        data["category_name"] = category
        data["total_students"] = total_students
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

@frappe.whitelist(methods=["POST"])
def create_course():
    try:
        data = frappe.request.get_json() or {}
        print(data)
        instructor = data.get("instructor")
        course_title = data.get("course_title")
        category = data.get("category")
        description = data.get("description")
        thumbnail = data.get("thumbnail")
        price_type = data.get("price_type")
        price = data.get("price")
        level = data.get("level")
        status = data.get("status")

        if not all([instructor, course_title, category, price_type, level]):
            response_maker(
                desc="Бүх талбарыг бөглөнө үү.",
                status=400,
                type="error",
            )
            return
        
        existing_course = frappe.db.exists("Course", {"course_title": course_title})
        
        if existing_course:
            return response_maker(
                desc="Ижил нэртэй сургалт бүртгэгдсэн байна.",
                status=409,
                type="error",
            )

        course = frappe.get_doc({
            "doctype": "Course",
            "instructor": instructor,
            "course_title": course_title,
            "category": category,
            "description": description,
            "thumbnail": thumbnail,
            "price_type": price_type,
            "price": price,
            "level": level,
            "status": status
        })
        course.flags.ignore_mandatory = True

        course.insert()

        response_maker(
            desc="Сургалт амжилттай бүртгэгдлээ.",
            status=201
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
    
@frappe.whitelist(allow_guest=False, methods=["PUT"])
def update_course():
    try:
        data = frappe.request.request.get_json() or {}
        course = frappe.get_doc("Course", {"name": data.get("courseId")})
        user = frappe.session.user
        if user.name == course.instructor:
            for field, value in data.items():
                if field == "courseId":
                    continue
                if field in course.as_dict(): 
                    setattr(course, field, value)

            course.save()
            response_maker(
                desc="Амжилттай засагдлаа.",
                status=201
            )
        else:
            response_maker(
                desc="Сургалт засах эрхгүй байна.",
                status=401,
                type="error"
            )
    except:
        response_maker(
            desc="Сургалт засахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        frappe.log_error(frappe.get_traceback(), "Create Course Error")
        print(frappe.get_traceback())
        return
    return 


@frappe.whitelist(methods=["DELETE"])
def delete_course():
    try:
        id = frappe.request.args.get("id")
        if not id:
            response_maker(
                desc="Сургалтын ID байхгүй байна.",
                status=404,
                type="error"
            )
        if not frappe.db.exists("Course", id):
            return response_maker(
                desc="Сургалт олдсонгүй.",
                status=404,
                type="error"
            )
        frappe.delete_doc("Course", id)
        response_maker(
            desc="Сургалт амжилттай устгагдлаа."
        )
    except Exception as e:
        print(frappe.get_traceback())
        response_maker(
            desc="Сургалт устгахад алдаа гарлаа.",
            status=e.status_code,
            type="error"
        )
        return