import frappe
from lms_app.utils.utils import response_maker

@frappe.whitelist(methods=["GET"])
def get_student_profile():
    user = frappe.session.user

    roles = frappe.get_roles(user)
    if "Student" not in roles:
        response_maker(
            desc="Хэрэглэгч нь суралцагч биш байна.",
            status=403,
            type="error"
        )
        return
    try:
        student = frappe.get_doc("Student_profile", {"user": user})
        student_user = frappe.get_value("User", user, ["name", "email", "first_name", "last_name", "phone", "user_image"], as_dict=True)
        profile_data = {
            "school": student.school,
            "education_level": student.education_level,
            "first_name": student_user.first_name,
            "last_name": student_user.last_name,
            "email": student_user.email,
            "phone": student_user.phone,
            "profile": student_user.user_image
        }
        response_maker(
            desc="Суралцагчийн профайлыг амжилттай авлаа.",
            data=profile_data
        )
        return
    except:
        print(frappe.get_traceback())
        response_maker(
            desc="Суралцагчийн профайлыг авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return
    
@frappe.whitelist(methods=["PUT"])
def update_student_profile():
    user = frappe.session.user

    roles = frappe.get_roles(user)
    if "Student" not in roles:
        response_maker(
            desc="Хэрэглэгч нь суралцагч биш байна.",
            status=403,
            type="error"
        )
        return
    try:
        data = frappe.request.get_json() or {}
        
        student = frappe.get_doc("Student_profile", {"user": user})
        for field, value in data.items():
            if field in student.as_dict(): 
                setattr(student, field, value)
            student.save()
        
        student_user = frappe.get_doc("User", user)
        for field, value in data.items():
            if field in student_user.as_dict(): 
                setattr(student_user, field, value)
            student_user.save()
        response_maker(
            desc="Суралцагчийн профайлыг амжилттай шинэчиллээ."
        )
        return
    except:
        print(frappe.get_traceback())
        response_maker(
            desc="Суралцагчийн профайлыг шинэчлэхэд алдаа гарлаа.",
            status=500,
            type="error"
        )
        return