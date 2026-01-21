import frappe
from lms_app.utils.utils import response_maker
from lms_app.api.enrollment import check_enrollment

@frappe.whitelist(methods=["GET"])
def get_quiz_submissions(quizId = None, courseId = None):
    user = frappe.session.user
    if not quizId:
        response_maker(
            desc="Шалгалтын ID байхгүй байна.",
            status=400,
            type="error"
        )
        return
    if not check_enrollment(user, courseId):
        response_maker(
            desc="Шалгалтын оролдлогуудад хандах эрхгүй хэрэглэгч байна.",
            status=403,
            type="error"
        )
        return
    try:
        submissions = frappe.get_list(
            "Quiz_submission",
            filters={"quiz": quizId},
            fields=["name", "student", "score", "passed", "score_percent", "creation"]
        )
        response_maker(
            desc="Шалгалтын илгээвэрүүдийг амжилттай авлаа.",
            data=submissions
        )
        return
    except:
        frappe.log_error(frappe.get_traceback(), "Get submissions error")
        print(frappe.get_traceback())
        response_maker(
            desc="Шалгалтын илгээвэрүүдийг авахад алдаа гарлаа.",
            status=500,
            type="error"
        )
        return
    
@frappe.whitelist(methods=["POST"])
def create_quiz_submission(quizId = None, courseId=None, student_answers = None):
    user = frappe.session.user
    try:
        if not check_enrollment(user, courseId):
            response_maker(
                desc="Шалгалтын оролдлого үүсгэх эрхгүй хэрэглэгч байна.",
                status=403,
                type="error"
            )
            return
        
        quiz_questions = frappe.get_list(
            "Quiz_question",
            filters={"quiz": quizId},
            fields=["name", "question_text", "order", "score"]
        )
        
        correct_questions = []
        
        for q in quiz_questions:
            user_answer = next((ans for ans in student_answers if ans["quiz_question"] == q["name"]), None)
            correct_answer = frappe.get_value("Quiz_question_answer", {"parent": q["name"], "is_correct": 1}, "name")
            if user_answer and user_answer.get("quiz_question_answer") == correct_answer:
                correct_questions.append(q)
                
        score = sum(q["score"] for q in correct_questions)
        total_score, passing_score = frappe.get_value("Quiz", quizId, ["total_score", "passing_score"])
        score_percent = (score/total_score) * 100
        passed =  score_percent >= passing_score
        print(passed)
        submission = frappe.get_doc({
            "doctype": "Quiz_submission",
            "quiz": quizId,
            "student": user,
            "score": score,
            "student_answers": student_answers,
            "passed": passed,
            "score_percent": score_percent
        })
        submission.insert()
        response_maker(
            desc="Шалгалтын оролдлого амжилттай үүсгэлээ."
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