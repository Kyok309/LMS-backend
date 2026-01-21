import frappe
from lms_app.utils.utils import response_maker
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count
from lms_app.api.enrollment import check_enrollment


def check_instructor(quiz_id):
    user = frappe.session.user

    Quiz = DocType("Quiz")
    Lesson = DocType("Lesson")
    Course = DocType("Course")
    
    instructor = (
        frappe.qb
        .from_(Quiz)
        .join(Lesson)
        .on(Quiz.lesson == Lesson.name)
        .join(Course)
        .on(Lesson.course == Course.name)
        .select(
            Course.instructor
        )
        .where(
            Quiz.name == quiz_id
        )
    ).run(as_dict = True)

    return user == instructor[0]["instructor"]

@frappe.whitelist(methods=["GET"])
def get_quiz_instructor(quizId = None):
    if not quizId:
        response_maker(
            desc="Шалгалтын ID байхгүй байна.",
            status=400,
            type="error"
        )
        return
    if not check_instructor(quizId):
        response_maker(
            desc="Шалгалтын мэдээлэл авах эрхгүй байна.",
            status=403,
            type="error"
        )
        return
    if not frappe.db.exists("Quiz", quizId):
        response_maker(
            desc="Шалгалт олдсонгүй.",
            status=404,
            type="error"
        )
        return
    try:
        quiz = frappe.get_value(
            "Quiz",
            quizId,
            ["name", "title", "description", "passing_score", "time_limit_minutes", "total_score", "creation", "modified"],
            as_dict=1
        )
        quiz_questions = frappe.get_list(
            "Quiz_question",
            filters={"quiz": quizId},
            fields=["question_text", "question_file", "order", "passing_score", "time_limit_minutes", "creation", "modified"]
        )
        data= quiz
        data["quiz_questions"] = quiz_questions
        response_maker(
            desc="Шалгалтын мэдээлэл амжилттай авлаа.",
            data=data
        )
        return
    except frappe.DoesNotExistError:
        response_maker(
            desc="Шалгалт олдсонгүй.",
            status=404,
            type="error"
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get quiz instructor error")
        print(frappe.get_traceback())
        response_maker(
            desc="Шалгалтын мэдээлэл авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return

@frappe.whitelist(methods=["GET"])
def get_quizzes_instructor(lessonId = None):
    try:
        user = frappe.session.user
        if user == frappe.get_value("Lesson", lessonId, "owner"):
            quizzes = frappe.get_list(
            "Quiz",
            filters={"lesson": lessonId},
            fields=["name", "title", "description", "passing_score", "time_limit_minutes"]
            )
            response_maker(
                desc="Шалгалтын жагсаалт амжилттай авлаа.",
                data=quizzes
            )
            return
        else:
            response_maker(
                desc="Шалгалтын жагсаалт авах эрхгүй хэрэглэгч байна.",
                status=403,
                type="error"
            )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get quizzes instructor error")
        print(frappe.get_traceback())
        response_maker(
            desc="Шалгалтын жагсаалт авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return
    
@frappe.whitelist(methods=["GET"])
def get_quiz(quizId = None, courseId = None):
    try:
        print(quizId)
        user = frappe.session.user
        if check_enrollment(user, courseId):
            quiz = frappe.get_value(
                "Quiz",
                quizId,
                ["name", "title", "description", "passing_score", "time_limit_minutes", "total_score"],
                as_dict=1
            )
            print(quiz)
            response_maker(
                desc="Шалгалтын мэдээллийг амжилттай авлаа.",
                data=quiz
            )
            return
        else:
            response_maker(
                desc="Уг сургалтанд элсээгүй байна.",
                status=403,
                type="error"
            )
            return
    except frappe.DoesNotExistError:
        response_maker(
            desc="Шалгалт олдсонгүй.",
            status=404,
            type="error"
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get quiz error")
        print(frappe.get_traceback())
        response_maker(
            desc="Шалгалтын мэдээлэл авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
    
@frappe.whitelist(methods=["GET"])
def get_quizzes(lessonId = None):
    try:
        user = frappe.session.user
        course = frappe.get_value("Lesson", lessonId, "course")
        if check_enrollment(user, course):
            quizzes = frappe.get_list(
            "Quiz",
            filters={"lesson": lessonId},
            fields=["name", "title", "description", "total_score", "passing_score", "time_limit_minutes"]
            )
            response_maker(
                desc="Шалгалтын жагсаалт амжилттай авлаа.",
                data=quizzes
            )
            return
        else:
            response_maker(
                desc="Уг сургалтанд элсээгүй байна.",
                status=403,
                type="error"
            )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get quizzes error")
        print(frappe.get_traceback())
        response_maker(
            desc="Шалгалтын жагсаалт авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return
    
@frappe.whitelist(methods=["POST"])
def create_quiz(lesson = None, title = None, description = None, passing_score = None, time_limit_minutes = None):
    user = frappe.session.user
    if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
        response_maker(
            desc="Шалгалт үүсгэх эрхгүй хэрэглэгч байна.",
            status=403,
            type="error"
        )
        return
    if not all([lesson, title, time_limit_minutes]):
        response_maker(
            desc="Шалгалтын мэдээлэл дутуу байна.",
            status=400,
            type="error"
        )
        return
    try:
        quiz = frappe.get_doc({
            "doctype": "Quiz",
            "lesson": lesson,
            "title": title,
            "description": description,
            "passing_score": passing_score,
            "time_limit_minutes": time_limit_minutes
        })
        quiz.insert()
        response_maker(
            desc="Шалгалт амжилттай хадгалагдлаа.",
            status=201
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Create quiz error")
        print(frappe.get_traceback())
        response_maker(
            desc="Шалгалт үүсгэхэд алдаа гарлаа.",
            status=500,
            type="error"
        )
        return
    
@frappe.whitelist(methods=["PUT"])
def update_quiz(quizId=None, title=None, description=None, passing_score=None, time_limit_minutes=None):
    if not quizId:
        response_maker(
            desc="Шалгалтын ID байхгүй байна.",
            status=400,
            type="error"
        )
        return
    if not all([title, passing_score, time_limit_minutes]):
        response_maker(
            desc="Бүх талбарыг бөглөнө үү.",
            status=400,
            type="error"
        )
        return
    
    if not check_instructor(quizId):
        response_maker(
            desc="Шалгалт засах эрхгүй хэрэглэгч байна.",
            status=403,
            type="error"
        )
        return
    
    try:
        quiz = frappe.get_doc("Quiz", quizId)
        quiz.update({
            "title": title,
            "description": description,
            "passing_score": passing_score,
            "time_limit_minutes": time_limit_minutes
        })
        quiz.save()
        response_maker(
            desc="Шалгалт амжилттай засагдлаа."
        )
        return
    except frappe.DoesNotExistError:
        response_maker(
            desc="Шалгалт олдсонгүй.",
            status=404,
            type="error"
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Update quiz error")
        print(frappe.get_traceback())
        response_maker(
            desc="Шалгалт засахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return
    
@frappe.whitelist(methods=["DELETE"])
def delete_quiz(quizId = None):
    if not quizId:
        response_maker(
            desc="Шалгалтын ID байхгүй байна.",
            status=400,
            type="error"
        )
        return
    if not check_instructor(quizId):
        response_maker(
            desc="Шалгалтыг устгах эрхгүй байна.",
            status=403,
            type="error"
        )
        return
    try:
        quiz = frappe.get_doc("Quiz", quizId)
        quiz.delete()
        response_maker(
            desc="Шалгалт амжилттай устлаа."
        )
        return
    except frappe.DoesNotExistError:
        response_maker(
            desc="Шалгалт олдсонгүй.",
            status=404,
            type="error"
        )
        return
    except:
        frappe.log_error(frappe.get_traceback, "Quiz delete error")
        print(frappe.get_traceback())
        response_maker(
            desc="Шалгалт устгахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return