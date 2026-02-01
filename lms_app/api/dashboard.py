import frappe
from lms_app.utils.utils import response_maker
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Sum, Avg, NullIf, IfNull
from frappe.query_builder import Case

Category = DocType("Category")
Course = DocType("Course")
Enrollment = DocType("Enrollment")
Payment = DocType("Payment")
Lesson = DocType("Lesson")
Lesson_student = DocType("Lesson_student")

@frappe.whitelist(methods=["GET"])
def get_dashboard_instructor():
   user = frappe.session.user
   if not frappe.db.exists("Has Role", {"parent": user, "role": "Insturctor"}):
      response_maker(
         desc="Хяналтын самбарын мэдээлэл авах эрхгүй хэрэглэгч байна.",
         status=403,
         type="error"
      )
   try:
      total_enrollments=(frappe.qb
         .from_(Enrollment)
         .join(Course)
         .on(Course.name == Enrollment.course)
         .select(Course.course_title, Count(Enrollment.name).as_("enrollment"))
         .where(Course.instructor == user)
         .groupby(Course.course_title)
      ).run(as_dict=True)

      total_revenue = (frappe.qb
         .from_(Payment)
         .join(Course)
         .on(Course.name == Payment.course)
         .select(Course.course_title, Sum(Payment.amount).as_("revenue"))
         .where(Course.instructor == user)
         .groupby(Course.course_title)
      ).run(as_dict=True)

      total_lessons = (frappe.qb
         .from_(Course)
         .join(Lesson)
         .on(Lesson.course == Course.name)
         .select(Course.course_title, Count(Lesson.name).as_("lessons"))
         .where(Course.instructor == user)
         .groupby(Course.course_title)
      ).run(as_dict=True)
      
      average_score_course = (frappe.qb
         .from_(Course)
         .join(Lesson)
         .on(Course.name == Lesson.course)
         .join(Lesson_student)
         .on(Lesson.name == Lesson_student.lesson)
         .select(Course.course_title, Avg(Lesson_student.final_score).as_("avg"))
         .where(Course.instructor == user)
         .groupby(Course.course_title)
      ).run(as_dict=True)

      query = """
         SELECT
            m.month,
            COALESCE(COUNT(e.name), 0) AS count
         FROM (
            SELECT DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL n MONTH), '%Y-%m') AS month
            FROM (
               SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2
               UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
            ) numbers
         ) m
         LEFT JOIN `tabEnrollment` e
            ON DATE_FORMAT(e.creation, '%Y-%m') = m.month
         GROUP BY m.month
         ORDER BY m.month
      """

      enrollment_month = frappe.db.sql(query, as_dict=True)

      completion_rate = (
         frappe.qb
            .from_(Course)
            .left_join(Enrollment)
            .on(Course.name == Enrollment.course)
            .select(
               Course.course_title,

               Count(Enrollment.name).as_("total_enrollments"),

               Sum(
                  Case()
                     .when(Enrollment.completion_status == "Finished", 1)
                     .else_(0)
               ).as_("finished_enrollments"),

               IfNull(
                  Sum(
                     Case()
                        .when(Enrollment.completion_status == "Finished", 1)
                        .else_(0)
                  ) / NullIf(Count(Enrollment.name), 0) * 100, 0
               ).as_("completion_rate")
            )
            .where(Course.instructor == user)
            .groupby(Course.course_title)
      ).run(as_dict=True)

      data = {
         "total_enrollments": total_enrollments,
         "total_revenue": total_revenue,
         "total_lessons": total_lessons,
         "average_score_course": average_score_course,
         "enrollment_month": enrollment_month,
         "completion_rate": completion_rate
      }

      response_maker(
         desc="Хяналтын самбарын мэдээлэл амжилттай авлаа.",
         data=data
      )

   except:
      frappe.log_error(frappe.get_traceback(), "Get dashboard instructor error")
      print(frappe.get_traceback())
      response_maker(
         desc="Хяналтын самбарын мэдээлэл авахад алдаа гарлаа.",
         status=500,
         type="error"
      )

@frappe.whitelist(methods=["GET"])
def get_dashboard():
   user = frappe.session.user
   if not frappe.db.exists("Has Role", {"parent": user, "role": "Student"}):
      response_maker(
         desc="Хяналтын самбарын мэдээлэл авах эрхгүй хэрэглэгч байна.",
         status=403,
         type="error"
      )
   try:
      enrolled_courses = frappe.db.count("Enrollment", {"student": user})
      finished_lessons = frappe.db.count("Lesson_student", {"status": "Done", "student": user})
      finished_courses = frappe.db.count("Enrollment", {"completion_status": "Finished", "student": user})
      average_score = (frappe.qb
         .from_(Enrollment)
         .select(Avg(Enrollment.average_score).as_("avg_score"))
         .where(Enrollment.student == user)
      ).run()[0][0]
      completion_rate = finished_courses / enrolled_courses * 100

      completed_lesson_week = frappe.db.sql(
         """
         SELECT
            YEARWEEK(modified, 1) AS year_week,
            DATE_SUB(DATE(modified), INTERVAL WEEKDAY(modified) DAY) AS week_start,
            DATE_ADD(
                  DATE_SUB(DATE(modified), INTERVAL WEEKDAY(modified) DAY),
                  INTERVAL 6 DAY
            ) AS week_end,
            COUNT(*) AS done_count
         FROM `tabLesson_student`
         WHERE
            status = 'Done'
            AND modified >= DATE_SUB(CURDATE(), INTERVAL 6 WEEK)
            AND student = %(user)s
         GROUP BY YEARWEEK(modified, 1)
         ORDER BY year_week
         """,
         {"user": user},
         as_dict=True
      )
      for row in completed_lesson_week:
         row["label"] = f"{row['week_start']} - {row['week_end']}"

      course_category = (frappe.qb
         .from_(Category)
         .join(Course)
         .on(Course.category == Category.name)
         .join(Enrollment)
         .on(Enrollment.course == Course.name)
         .select(Category.category_name, Count(Course.name).as_("courses"))
         .where(Enrollment.student == user)
         .groupby(Category.category_name)
      ).run(as_dict=True)

      progress_category = (frappe.qb
         .from_(Category)
         .join(Course)
         .on(Category.name == Course.category)
         .join(Enrollment)
         .on(Enrollment.course == Course.name)
         .select(Category.category_name, Avg(Enrollment.progress_percentage).as_("progress"))
         .where(Enrollment.student == user)
         .groupby(Category.category_name)
      ).run(as_dict=True)

      avg_course = (frappe.qb
         .from_(Enrollment)
         .join(Course)
         .on(Enrollment.course == Course.name)
         .select(Course.course_title, Enrollment.average_score)
         .where(Enrollment.student == user)
      ).run(as_dict=True)

      data = {
         "enrolled_courses": enrolled_courses,
         "finished_lessons": finished_lessons,
         "finished_courses": finished_courses,
         "average_score": average_score,
         "completion_rate": completion_rate,
         "completed_lesson_week": completed_lesson_week,
         "avg_course": avg_course,
         "course_category": course_category,
         "progress_category": progress_category
      }

      response_maker(
         desc="Хяналтын самбарын мэдээлэл амжилттай авлаа.",
         data=data
      )
   except:
      frappe.log_error(frappe.get_traceback(), "Get dashboard error")
      print(frappe.get_traceback())
      response_maker(
         desc="Хяналтын самбарын мэдээлэл авахад алдаа гарлаа.",
         status=500,
         type="error"
      )