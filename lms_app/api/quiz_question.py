import frappe
from lms_app.utils.utils import response_maker
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count
import traceback
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
def get_quiz_questions(quizId = None, courseId = None):
   import random
   
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
         desc="Шалгалтын асуултуудад хандах эрхгүй хэрэглэгч байна.",
         status=403,
         type="error"
      )
      return
   try:
      quiz_questions = frappe.db.sql("""
         SELECT
            q.name,
            q.question_text,
            q.`order`,
            q.score,
            JSON_ARRAYAGG(
                  JSON_OBJECT(
                     'name', a.name,
                     'answer_text', a.answer_text,
                     'is_correct', a.is_correct
                  )
            ) AS quiz_question_answer
         FROM `tabQuiz_question` q
         JOIN `tabQuiz_question_answer` a
            ON a.parent = q.name
         WHERE q.quiz = %s
         GROUP BY q.name
      """, quizId, as_dict=True)

      for q in quiz_questions:
         q['quiz_question_answer'] = frappe.parse_json(q['quiz_question_answer'])
         random.shuffle(q['quiz_question_answer'])  # Shuffle answers for each question
      
      print(quiz_questions)
      response_maker(
         desc="Шалгалтын асуултуудыг амжилттай авлаа.",
         data=quiz_questions
      )
      return
   except:
      frappe.log_error(frappe.get_traceback(), "Get quiz questions error")
      print(frappe.get_traceback())
      response_maker(
         desc="Шалгалтын асуултуудыг авахад алдаа гарлаа.",
         status=500,
         type="error"
      )
      return

@frappe.whitelist(methods=["GET"])
def get_quiz_questions_instructor(quizId = None):
   if not quizId:
      response_maker(
         desc="Хичээлийн ID байхгүй байна.",
         status=400,
         type="error"
      )
      return
   if not check_instructor(quizId):
      response_maker(
         desc="Шалгалтын мэдээлэлд хандах эрхгүй хэрэглэгч байна.",
         status=403,
         type="error"
      )
      return
   try:
      quiz_questions = frappe.get_list(
         "Quiz_question",
         filters={"quiz": quizId},
         fields=["name", "question_text", "order", "score"],
         order_by="`order` asc"
      )
      print(quiz_questions)
      response_maker(
         desc="Шалгалтын асуултуудыг амжилттай авлаа.",
         data=quiz_questions
      )
      return
   except:
      frappe.log_error(frappe.get_traceback(), "Get quiz questions error")
      print(frappe.get_traceback())
      response_maker(
         desc="Шалгалтын асуултуудыг авахад алдаа гарлаа.",
         status=500,
         type="error"
      )
      return
   
@frappe.whitelist(methods=["GET"])
def get_quiz_question_instructor(quizId = None, questionId = None):
   if not questionId:
      response_maker(
         desc="Шалгалтын асуултын ID байхгүй байна.",
         status=400,
         type="error"
      )
   if not check_instructor(quizId):
      response_maker(
         desc="Шалгалтын мэдээлэлд хандах эрхгүй хэрэглэгч байна.",
         status=403,
         type="error"
      )
   try:
      quiz_question = frappe.get_doc("Quiz_question", questionId)
      response_maker(
         desc="Шалгалтын асуултын мэдээллийг амжилттай авлаа.",
         data=quiz_question
      )
   except frappe.DoesNotExistError:
      response_maker(
         desc="Шалгалтын асуулт олдсонгүй.",
         status=404,
         type="error"
      )
      return
   except:
      frappe.log_error(frappe.get_traceback(), "Get quiz question instructor error")
      print(frappe.get_traceback())
      response_maker(
         desc="Шалгалтын асуултын мэдээлэл авахад алдаа гарлаа.",
         status=500,
         type="error"
      )
    
@frappe.whitelist(methods=["POST"])
def create_quiz_question(quizId= None, question_text=None, question_file=None, order=None, score=0, quiz_question_answer=[]):
   if not all([quizId, question_text, order, score]):
      response_maker(
         desc="Бүх талбарыг бөглөнө үү.",
         status=400,
         type="error"
      )
      return
   user = frappe.session.user
   if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
      response_maker(
         desc="Асуулт үүсгэх эрхгүй хэрэглэгч байна.",
         status=403,
         type="error"
      )
      return
   try:
      quiz_question = frappe.get_doc({
         "doctype": "Quiz_question",
         "quiz": quizId,
         "question_text": question_text,
         "question_file": question_file,
         "order": order,
         "score": score,
         "quiz_question_answer": quiz_question_answer
      })
      quiz_question.save()
      response_maker(
         desc="Асуултыг амжилттай бүртгэлээ.",
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
      print(traceback.format_exc())
      frappe.log_error(frappe.get_traceback(), "Create quiz question error")
      response_maker(
         desc="Асуулт бүртгэхэд алдаа гарлаа.",
         status=500,
         type="error"
      )
      return
    
@frappe.whitelist(methods=["PUT"])
def update_quiz_question(questionId=None, quiz=None, question_text=None, question_file=None, order=None, score=None, quiz_question_answer=None):
   if not all([questionId, quiz, question_text, order, score]):
      response_maker(
         desc="Бүх талбарыг бөглөнө үү.",
         status=400,
         type="error"
      )
      return
   if not check_instructor(quiz):
      response_maker(
         desc="Асуулт засах эрхгүй хэрэглэгч байна.",
         status=403,
         type="error"
      )
      return
   try:
      question = frappe.get_doc("Quiz_question", questionId)
      question.update({
         "question_text": question_text,
         "question_file": question_file,
         "order": order,
         "score": score,
         "quiz_question_answer": quiz_question_answer
      })
      question.save()
      response_maker(
         desc="Асуулт амжилттай засагдлаа."
      )
      return
   except frappe.DoesNotExistError:
      response_maker(
         desc="Асуулт олдсонгүй.",
         status=404,
         type="error"
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
      response_maker(
         desc="Асуулт засахад алдаа гарлаа.",
         status=500,
         type="error"
      )
      return

@frappe.whitelist(methods=["DELETE"])
def delete_quiz_question(questionId = None):
   if not questionId:
      response_maker(
         desc="Асуултын ID байхгүй байна.",
         status=400,
         type="error"
      )
      return
   try:
      question = frappe.get_doc("Quiz_question", questionId)
      if not check_instructor(question.quiz):
         response_maker(
               desc="Асуулт устгах эрхгүй хэрэглэгч байна.",
               status=403,
               type="error"
         )
         return
      question.delete()
      frappe.db.commit()
      response_maker(
         desc="Асуулт амжилттай устгагдлаа."
      )
      return
   except frappe.DoesNotExistError:
      response_maker(
         desc="Асуулт олдсонгүй.",
         status=404,
         type="error"
      )
      return
   except:
      frappe.log_error(frappe.get_traceback(), "Delete quiz question error")
      print(frappe.get_traceback())
      response_maker(
         desc="Асуулт устгахад алдаа гарлаа.",
         status=500,
         type="error"
      )