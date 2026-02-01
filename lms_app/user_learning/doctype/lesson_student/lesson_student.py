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
		completed_lessons = frappe.get_all(
			"Lesson_student",
			filters={
				"lesson.course": course_name,
				"student": self.student,
				"status": "Done"
			},
			fields=["name"]
		)
		total_lesson_student = frappe.db.count("Lesson_student", {"lesson.course": course_name, "student": self.student})
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
		final_scores = frappe.get_all("Lesson_student",
         filters={"lesson.course": course_name, "student": self.student, "final_score": ["!=", 0]},
         fields=["final_score"])
		print(len(final_scores))
		
		# Average_score
		average = sum(d.final_score for d in final_scores) / len(final_scores)
		frappe.db.set_value("Enrollment", {"course": course_name, "student": self.student}, "average_score", average)