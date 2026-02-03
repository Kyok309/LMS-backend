# Copyright (c) 2026, urtaa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe


class Lesson_student(Document):
	def on_update(self):
		if self.status == "Done":
			self.calculate_progress()
			self.calculate_average_score()
   
	def calculate_progress(self):
		course_name = frappe.get_value("Lesson", self.lesson, "course")
		enrollment = frappe.get_doc("Enrollment", {"course": course_name, "student": self.student})

		# Progress %
		completed_lessons = frappe.db.sql(
			"""
			SELECT ls.name
			FROM `tabLesson_student` ls
			INNER JOIN `tabLesson` l ON l.name = ls.lesson
			WHERE l.course = %s
				AND ls.student = %s
				AND ls.status = %s
			""",
			(course_name, self.student, "Done"),
			as_dict=True
		)

		total_lesson_student = frappe.db.sql(
			"""
			SELECT COUNT(*)
			FROM `tabLesson_student` ls
			INNER JOIN `tabLesson` l ON l.name = ls.lesson
			WHERE l.course = %s
				AND ls.student = %s
			""",
			(course_name, self.student)
		)[0][0]

		progress = len(completed_lessons)/total_lesson_student * 100

		# Completion_status -> Finished
		if len(completed_lessons) == total_lesson_student:
			enrollment.update({
				"completion_status": "Finished"
			})
   
		# Completed_lessons
		enrollment.update({
			"completed_lessons": len(completed_lessons),
			"progress_percentage": progress
		})
		enrollment.save(ignore_permissions=True)
	
	def calculate_average_score(self):
		course_name = frappe.get_value("Lesson", self.lesson, "course")
		final_scores = frappe.db.sql(
			"""
			SELECT ls.final_score
			FROM `tabLesson_student` ls
			INNER JOIN `tabLesson` l ON l.name = ls.lesson
			WHERE l.course = %s
				AND ls.student = %s
				AND ls.final_score != 0
			""",
			(course_name, self.student),
			as_dict=True
		)

		# Average_score
		average = sum(d.final_score for d in final_scores) / len(final_scores)
		frappe.db.set_value("Enrollment", {"course": course_name, "student": self.student}, "average_score", average)