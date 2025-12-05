import frappe
from lms_app.utils.utils import response_maker

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_courses():
    try:
        # Get filter parameters from request
        categories = frappe.request.args.get("categories")
        min_price = frappe.request.args.get("min_price", 0, type=int)
        max_price = frappe.request.args.get("max_price", 1000000, type=int)
        sort_by = frappe.request.args.get("sort_by", "creation_desc")
        page = frappe.request.args.get("page", 1, type=int)
        search_query = frappe.request.args.get("search", "")
        
        # Parse categories (comma-separated string)
        category_list = [c.strip() for c in categories.split(",")] if categories else []
        
        # Determine sort order
        field, direction = sort_by.rsplit("_", 1)
        order_by = f"{field} {direction}"
        
        # Build filters
        filters = {"status": "Published"}
        
        if category_list:
            filters["category"] = ["in", category_list]
        
        # Get all courses with filters (we'll filter by search and price after)
        all_courses = frappe.db.get_all(
            "Course",
            filters=filters,
            fields="*",
            order_by=order_by
        )
        
        # Filter by search query and price range, then enrich with data
        filtered_courses = []
        
        for course in all_courses:
            price = float(course.get("price", 0))
            
            # Check if price is within range
            if not (min_price <= price <= max_price):
                continue
            
            instructor_id = course.get("instructor")
            instructor_name = ""
            
            # Get instructor name for search
            if instructor_id:
                full_name, user_image = frappe.get_value("User", instructor_id, ["full_name", "user_image"])
                course["instructor_full_name"] = full_name
                course["instructor_image"] = user_image
                instructor_name = full_name or ""
            else:
                course["instructor_full_name"] = None
                course["instructor_image"] = None
            
            # Check if search query matches course title or instructor name
            if search_query:
                search_lower = search_query.lower()
                course_title = (course.get("course_title") or "").lower()
                instructor_lower = instructor_name.lower()
                
                if not (search_lower in course_title or search_lower in instructor_lower):
                    continue
            
            # Get category name
            category_id = course.get("category")
            if category_id:
                category_name = frappe.get_value("Category", category_id, "category_name")
                course["category_name"] = category_name
            else:
                course["category_name"] = None
            
            # Get counts
            student_count = frappe.db.count("Enrollment", {"course": course.get("name")})
            lesson_count = frappe.db.count("Lesson", {"course": course.get("name")})
            course["student_count"] = student_count
            course["lesson_count"] = lesson_count
            
            filtered_courses.append(course)
    
        
        # Pagination
        per_page = 9
        offset = (page - 1) * per_page
        total_count = len(filtered_courses)
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        paginated_courses = filtered_courses[offset:offset + per_page]
        
        response_maker(
            desc="Амжилттай",
            data={
                "courses": paginated_courses,
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
        return

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_courses_instructor():
    try:
        user = frappe.session.user
        courses = frappe.db.get_all("Course", filters={'status': 'Published', 'instructor': user}, fields="*")
        
        for course in courses:
            category_id = course.get("category")
            student_count = frappe.db.count("Enrollment", {"course": course.get("name")})
            lesson_count = frappe.db.count("Lesson", {"course": course.get("name")})
            if category_id:
                category_name = frappe.get_value("Category", category_id, "category_name")
                course["category_name"] = category_name
            else:
                course["category_name"] = None
            course["student_count"] = student_count
            course["lesson_count"] = lesson_count
        response_maker(
            desc="Амжилттай",
            data=courses
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
        instructor = frappe.get_value("User", course.instructor, "full_name")
        category = frappe.get_value("Category", course.category, "category_name")
        print(course)
        print(instructor)
        print(category)
        data = course.as_dict()
        data["instructor_name"] = instructor
        data["category_name"] = category
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

@frappe.whitelist(allow_guest=False, methods=["POST"])
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
    pass

@frappe.whitelist(allow_guest=False, methods=["DELETE"])
def delete_course():
    pass