import frappe
from lms_app.utils.utils import response_maker
from frappe.auth import check_password
import requests

@frappe.whitelist(allow_guest=True, methods=["POST"])
def signup():
    try:
        data = frappe.request.get_json() or {}
        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone = data.get("phone")
        password = data.get("password")
        role = data.get("role")

        print(data)

        if not all([email, first_name, last_name, phone, password, role]):
            response_maker(
                desc="Бүх талбарыг бөглөнө үү.",
                status=400,
                type="error",
            )
            return

        # Check if user exists
        existing_user = frappe.db.get_value(
            "User",
            {"email": email},
            "name"
        )

        if existing_user:
            # Check if this user already has the role
            if frappe.db.exists("Has Role", {"parent": existing_user, "role": role}):
                return response_maker(
                    desc="Тухайн рольтой хэрэглэгч бүртгэлтэй байна.",
                    status=409,
                    type="error",
                )

        # Create user
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "new_password": password,
            "send_welcome_email": 0,
            "enabled": 1,
        })

        user.flags.ignore_password_policy = True
        user.flags.ignore_mandatory = True

        user.insert(ignore_permissions=True)
        
        # Add Student role
        user.add_roles(role)
        
        if role == "Instructor":
            profile = frappe.get_doc({
                "doctype": "Instructor_profile",
                "user": user.name,
                "total_courses": 0,
                "rating": 0.0
            })
        elif role == "Student":
            profile = frappe.get_doc({
                "doctype": "Student_profile",
                "user": user.name,
                "total_enrollments": 0
            })

        profile.flags.ignore_permissions = True
        profile.insert()

        response_maker(
            desc="Амжилттай бүртгэгдлээ.",
            status=201,
            data={"user_email": user.name}
        )
        return
    except:
        response_maker(
            desc="Бүртгүүлэхэд алдаа гарлаа.",
            status=500,
            type="error",
        )
        frappe.log_error(frappe.get_traceback(), "Signup Error")
        return

@frappe.whitelist(allow_guest=True, methods=["POST"])
def login():
    try:
        data = frappe.request.get_json() or {}
        email = data.get("email")
        password = data.get("password")
        print(email, password)

        if not email or not password:
            response_maker(
                desc="И-мейл болон нууц үг шаардлагатай.",
                status=400,
                type="error",
            )
            return
       
        token_app = frappe.get_doc("OAuth Client", "3cvv8jgqe0")
        client_id = token_app.client_id
        client_secret = token_app.client_secret
        get_token_url = f"{frappe.utils.get_url()}/api/method/frappe.integrations.oauth2.get_token"
        body = {
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": email,
            "password": password
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(get_token_url, data=body, headers=headers, verify=False)
        print("Response received:", response.status_code, response.text)
        if response.status_code == 200:
            token_data = response.json()
            if "access_token" in token_data:
                user = frappe.db.get_value("User", {"email": email}, ["email", "first_name", "last_name", "phone", "user_image"], as_dict=1)
                roles = frappe.get_all(
                    "Has Role",
                    filters={"parent": email},
                    fields=["role"]
                )
                role_list = [r.role for r in roles]

                token_data["roles"] = role_list
                token_data["user"] = user

                response_maker(
                    desc="Амжилттай нэвтэрлээ.",
                    data=token_data
                )
                return
            else:
                response_maker(
                    desc="Нэвтрэх токен олдсонгүй.",
                    status=401,
                    type="error",
                )
                return
        else:
            response_maker(
                desc="И-мейл эсвэл нууц үг буруу байна.",
                status=response.status_code,
                type="error",
            )
            return
    except Exception as e:
        response_maker(
            desc=str(e),
            status=500,
            type="error",
        )
        frappe.log_error(frappe.get_traceback(), "Login Error")
        return
    
    
@frappe.whitelist(methods=["POST"])
def change_password(old_password, new_password):
    try:
        user = frappe.session.user
        if not user or user == "Guest":
            response_maker(
                desc="Нууц үг солих эрхгүй хэрэглэгч байна.",
                status=403,
                type="error"
            )
            return
        if old_password == new_password:
            response_maker(
                desc="Шинэ нууц үг хуучин нууц үгтэй ижил байна.",
                status=400,
                type="error"
            )
            return

        user_doc = frappe.get_doc("User", user)
        check_password(user, old_password)
        user_doc.new_password = new_password
        user_doc.save()
        response_maker(
            desc="Нууц үг амжилттай солигдлоо."
        )
        return
    except frappe.AuthenticationError:
        response_maker(
            desc="Хуучин нууц үг буруу байна.",
            status=400,
            type="error"
        )
        return
    except Exception as e:
        print(frappe.get_traceback())
        response_maker(
            desc=str(e),
            status=500,
            type="error"
        )
        frappe.log_error(frappe.get_traceback(), "Change Password Error")
        return
    
@frappe.whitelist(methods=["GET"])
def get_me():
    user = frappe.session.user
    roles = ["Student", "Instructor"]
    if not frappe.db.exists("Has Role", {"parent": user, "role": ["in", roles]}):
        response_maker(
            desc="Нэвтрээгүй хэрэглэгч байна.",
            status=401,
            type="error"
        )
        return
    try:
        user_info = frappe.get_value("User", user, ["first_name", "last_name", "full_name", "user_image", "email"], as_dict=1)
        response_maker(
            desc="Хэрэглэгчийн мэдээлэл амжилттай авлаа.",
            data=user_info
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get me error")
        print(frappe.get_traceback())
        response_maker(
            desc="Хэрэглэгчийн мэдээлэл авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return