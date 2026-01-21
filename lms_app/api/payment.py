import frappe
from lms_app.utils.utils import response_maker

def check_payment_status(course_id, student):
    payment_exists = frappe.db.exists(
        "Payment",
        {
            "course": course_id,
            "student": student,
            "payment_status": "Paid"
        }
    )
    return payment_exists

@frappe.whitelist(methods=["GET"])
def get_payments_student():
    user = frappe.session.user

    roles = frappe.get_roles(user)
    if "Student" not in roles:
        response_maker(
            desc="Төлбөрийн мэдээлэлд хандах эрхгүй байна.",
            status=403,
            type="error"
        )
        return
    try:
        payments = frappe.db.get_all(
            "Payment",
            filters={"student": user},
            fields=["course", "amount", "payment_status", "payment_method", "paid_on"]
        )
        course_ids = [p["course"] for p in payments]
        courses = frappe.db.get_all(
            "Course",
            filters={"name": ["in", course_ids]},
            fields=["name", "course_title"]
        )
        course_map = {c["name"]: c for c in courses}
        for payment in payments:
            course = course_map.get(payment["course"])
            payment["course_title"] = course["course_title"] if course else None

        total_sum = sum(p["amount"] for p in payments if p["payment_status"] == "Paid")
        print(total_sum)
        data={
            "payments": payments,
            "total_paid_amount": total_sum
        }
        response_maker(
            desc="Төлбөрийн мэдээллийг амжилттай авлаа.",
            data=data
        )
        return
    except:
        print(frappe.get_traceback())
        response_maker(
            desc="Төлбөрийн мэдээллийг авахад алдаа гарлаа.",
            status=500,
            type="error"
        )

@frappe.whitelist(methods=["GET"])
def get_payments_instructor():
    user = frappe.session.user
    if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
        response_maker(
            desc="Төлбөрийн мэдээлэлд хандах эрхгүй байна.",
            status=403,
            type="error"
        )
        return
    
    try:
        from frappe.query_builder import DocType
        from frappe.query_builder.functions import Count
        Student = DocType("User")
        Course = DocType("Course")
        Payment = DocType("Payment")
        
        payments = (
            frappe.qb
            .from_(Payment)
            .join(Student)
            .on(Payment.student == Student.name)
            .join(Course)
            .on(Payment.course == Course.name)
            .select(
                Payment.course, Payment.amount, Payment.payment_status, Payment.payment_method, Payment.paid_on, Course.name, Course.course_title, Student.full_name, Student.email
            )
            .where(
                Course.instructor == user
            )
        ).run(as_dict = True)

        total_sum = sum(p["amount"] for p in payments if p["payment_status"] == "Paid")
        data={
            "payments": payments,
            "total_paid_amount": total_sum
        }
        response_maker(
            desc="Төлбөрийн мэдээллийг амжилттай авлаа.",
            data=data
        )
        return
    except:
        print(frappe.get_traceback())
        response_maker(
            desc="Төлбөрийн мэдээллийг авахад алдаа гарлаа.",
            status=500,
            type="error"
        )