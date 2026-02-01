# Copyright (c) 2025, urtaa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class Quiz_submission(Document):
	def after_insert(self):
		self.update_lesson_student_final_score()
		self.update_lesson_student_status()
  
	def before_insert(self):
		self.update_enrollment_completion_status()
  
	def update_lesson_student_status(self):
		user = frappe.session.user
		if self.passed:
			lesson_name = frappe.get_value("Quiz", self.quiz, "lesson")
			lesson_student = frappe.get_doc("Lesson_student", {"lesson": lesson_name, "student": user})
			quiz = frappe.get_value("Quiz", {"lesson": lesson_name}, "name")
			
			if frappe.db.exists("Quiz_submission", {"quiz": quiz, "student": user, "passed": 1}):
				lesson_student.update({"status": "Done"})
			else:
				lesson_student.update({"status": "Open"})
			lesson_student.save(ignore_permissions=True)
	
	def update_lesson_student_final_score(self):
		if self.passed:
			lesson_name = frappe.get_value("Quiz", self.quiz, "lesson")
			lesson_student = frappe.get_doc("Lesson_student", {"lesson": lesson_name, "student": self.student})
			highest_score = frappe.get_value(
				"Quiz_submission",
				{"quiz": self.quiz, "student": self.student},
				"score_percent",
				order_by="score_percent desc"
			)
			print(highest_score)
			lesson_student.update({
				"final_score": highest_score or 0
			})
			lesson_student.save(ignore_permissions=True)
   
	def update_enrollment_completion_status(self):
		course = frappe.db.get_value(
			"Lesson",
			{"name": frappe.db.get_value("Quiz", self.quiz, "lesson")},
			"course"
		)
		
		has_submission = frappe.db.sql("""
			SELECT EXISTS (
				SELECT 1
				FROM `tabQuiz_submission` qs
				JOIN `tabQuiz` q ON q.name = qs.quiz
				JOIN `tabLesson` l ON l.name = q.lesson
				WHERE l.course = %s
			)
		""", course)[0][0]
		if has_submission:
			enrollment = frappe.get_doc("Enrollment", {"course": course, "student": self.student})
			enrollment.update({
				"completion_status": "In Progress"
			})
			enrollment.save(ignore_permissions=True)