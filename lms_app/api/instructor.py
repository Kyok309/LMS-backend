import frappe
from lms_app.utils.utils import response_maker
@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_instructor_profile():
    try:
        user = frappe.request.args.get("instructorId")
        
        instructor = frappe.get_value(
            "Instructor_profile",
            {"user": user},
            ["name", "profession", "expertise", "qualification", "experience", "total_courses", "rating"],
            as_dict=True
        )
        print(instructor)
        instructor_user = frappe.get_value(
            "User",
            user,
            ["email", "first_name", "last_name", "phone", "user_image", "bio"],
            as_dict=True
        )
        print(instructor_user)
        instructor.update(instructor_user)
        response_maker(
            desc="Багшийн профайлыг амжилттай авлаа.",
            data=instructor
        )
        return
    except:
        print(frappe.get_traceback())
        frappe.log_error(frappe.get_traceback(), "get instructor profile error")
        response_maker(
            desc="Багшийн профайлыг авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return
    
@frappe.whitelist(methods=["PUT"])
def update_instructor_profile():
    try:
        data = frappe.request.get_json() or {}
        user = frappe.session.user
        instructor = frappe.get_doc("Instructor_profile", {"user": user})
        if not instructor:
            response_maker(
                desc="Багшийн профайл олдсонгүй.",
                status=404,
                type="error"
            )
            return
        instructor_user = frappe.get_doc("User", user)
        if not instructor_user:
            response_maker(
                desc="Хэрэглэгч олдсонгүй.",
                status=404,
                type="error"
            )
            return
        
        for field, value in data.items():
            if hasattr(instructor, field):
                if field != "name":
                    instructor.set(field, value)
            elif hasattr(instructor_user, field):
                instructor_user.set(field, value)
        instructor.save()
        instructor_user.save()
        response_maker(
            desc="Багшийн профайлыг амжилттай шинэчиллээ."
        )
        return
    except Exception as e:
        print(frappe.get_traceback())
        frappe.log_error(frappe.get_traceback(), "update instructor profile error")
        response_maker(
            desc=str(e),
            status=500,
            type="error"
        )
        return