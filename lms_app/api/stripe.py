
import frappe
import stripe
from lms_app.utils.utils import response_maker
from lms_app.api.payment import check_payment_status

@frappe.whitelist(methods=["POST"])
def create_onboarding_link():
    try:
        stripe.api_key = frappe.conf.stripe_secret_key
        user = frappe.session.user
        instructor = frappe.get_doc("Instructor_profile", {"user": user})

        if instructor.connected_account_id:
            account_id = instructor.connected_account_id
        else:
            account = stripe.Account.create(type="standard")
            account_id = account.id
            instructor.connected_account_id = account_id
            instructor.save()

        link = stripe.AccountLink.create(
            account=account_id,
            refresh_url="http://localhost:3000/stripe/refresh",
            return_url="http://localhost:3000/instructor/settings",
            type="account_onboarding"
        )
        response_maker(
            desc="Onboarding link created successfully.",
            data={"url": link.url}
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
def create_checkout_session(course_id):
    student = frappe.session.user
    roles = frappe.get_roles(student)
    if "Student" not in roles:
        response_maker(
            desc="Захиалгын эрхгүй хэрэглэгч байна.",
            status=403,
            type="error"
        )
        return
    course = frappe.get_doc("Course", course_id)
    instructor = frappe.get_doc("Instructor_profile", {"user": course.instructor})
    
    already_bought = check_payment_status(course_id, student)
    if already_bought:
        response_maker(
            desc="Та энэ сургалтыг аль хэдийн худалдаж авсан байна.",
            status=400,
            type="error"
        )
        return
    try:
        stripe.api_key = frappe.conf.stripe_secret_key

        platform_fee = int(course.price * 0.1 * 100)

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "mnt",
                    "product_data": {"name": course.course_title},
                    "unit_amount": int(course.price * 100)
                },
                "quantity": 1
            }],
            payment_intent_data={
                "transfer_data": {
                    "destination": instructor.connected_account_id
                },
                "application_fee_amount": platform_fee
            },
            metadata={
                "course_id": course_id,
                "student": student
            },
            success_url="http://localhost:3000/profile/enrollments",
            cancel_url="http://localhost:3000/"
        )

        response_maker(
            desc="Checkout session created successfully.",
            data={"session_url": session.url}
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
    
@frappe.whitelist(allow_guest=True)
def stripe_webhook():
    payload = frappe.request.data
    sig = frappe.get_request_header("Stripe-Signature")
    stripe.api_key = frappe.conf.stripe_secret_key

    event = stripe.Webhook.construct_event(
        payload,
        sig,
        frappe.conf.stripe_webhook_secret
    )

    if event["type"] == "checkout.session.completed":
        s = event["data"]["object"]

        payment = frappe.get_doc({
            "doctype": "Payment",
            "course": s.metadata.course_id,
            "student": s.metadata.student,
            "amount": s.amount_total / 100,
            "payment_method": "Stripe",
            "payment_status": "Paid",
            "stripe_payment_id": s.payment_intent
        }).insert(ignore_permissions=True)

        frappe.get_doc({
            "doctype": "Enrollment",
            "course": s.metadata.course_id,
            "student": s.metadata.student,
            "payment": payment.name
        }).insert(ignore_permissions=True)

        frappe.db.commit()

    return "ok"