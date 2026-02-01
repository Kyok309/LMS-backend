import frappe
from lms_app.utils.utils import response_maker
from lms_app.api.enrollment import check_enrollment
from frappe.query_builder import DocType

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_reviews_course(courseId = None):
    if not courseId:
        response_maker(
            desc="Сургалтын ID байхгүй байна.",
            status=400,
            type="error"
        )
        return
    try:
        reviews = frappe.db.sql("""
            SELECT r.name, r.student, r.rating, r.review_text, r.creation, u.full_name, u.user_image
            FROM `tabReview` r
            JOIN `tabUser` u ON r.student = u.name
            WHERE r.course = %s
        """, (courseId,), as_dict=True)
        print(reviews)
        response_maker(
            desc="Сургалтын үнэлгээнүүдийг амжилттай авлаа.",
            data=reviews
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get reviews error")
        print(frappe.get_traceback())
        response_maker(
            desc="Сургалтын үнэлгээнүүдийг авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return
    
@frappe.whitelist(methods=["GET"])
def get_reviews_instructor(instructorId = None):
    try:
        Review = DocType("Review")
        Course = DocType("Course")
        User = DocType("User")
        reviews = (frappe.qb
            .from_(Review)
            .join(Course)
            .on(Course.name == Review.course)
            .join(User)
            .on(User.name == Review.student)
            .select(Review.rating, Review.review_text, Review.creation, Course.course_title, User.full_name, User.email, User.user_image)
            .where(Course.instructor == instructorId)
        ).run(as_dict=1)
        response_maker(
            desc="Үнэлгээний жагсаалт амжилттай авлаа.",
            data=reviews
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get reviews instructor error")
        print(frappe.get_traceback())
        response_maker(
            desc="Багшийн үнэлгээний жагсаалт авахад алдаа гарлаа.",
            status=500,
            type="error"
        )


@frappe.whitelist(methods=["POST"])
def create_review(courseId = None, rating = None, reviewText = None):
    user = frappe.session.user
    if not courseId:
        response_maker(
            desc="Сургалтын ID байхгүй байна.",
            status=400,
            type="error"
        )
        return
    if not check_enrollment(user, courseId):
        response_maker(
            desc="Сургалтын үнэлгээ үүсгэх эрхгүй хэрэглэгч байна.",
            status=403,
            type="error"
        )
        return
    if not rating:
        response_maker(
            desc="Үнэлгээний мэдээлэл дутуу байна.",
            status=400,
            type="error"
        )
        return
    if rating < 1 or rating > 5:
        response_maker(
            desc="Үнэлгээ 1-5 хооронд байх ёстой.",
            status=400,
            type="error"
        )
        return
    if frappe.db.exists("Review", {"course": courseId, "student": user}):
        response_maker(
            desc="Та уг сургалтанд аль хэдийн үнэлгээ өгсөн байна.",
            status=400,
            type="error"
        )
        return
    try:
        review = frappe.get_doc({
            "doctype": "Review",
            "course": courseId,
            "student": user,
            "rating": rating,
            "review_text": reviewText
        })
        review.insert()
        response_maker(
            desc="Сургалтын үнэлгээ амжилттай үүсгэлээ."
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
        frappe.log_error(frappe.get_traceback(), "Create review error")
        print(frappe.get_traceback())
        response_maker(
            desc="Сургалтын үнэлгээ үүсгэхэд алдаа гарлаа.",
            status=500,
            type="error"
        )
        return