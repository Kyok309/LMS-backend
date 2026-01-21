# Copyright (c) 2025, urtaa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class Enrollment(Document):
	def after_insert(self):
		self.create_lesson_students()
	
	def create_lesson_students(self):
		lessons = frappe.get_all("Lesson", filters={"course": self.course}, fields=["name"])
		for lesson in lessons:
			lesson_student = frappe.get_doc({
				"doctype": "Lesson_student",
				"lesson": lesson["name"],
				"student": self.student
			})
			lesson_student.insert(ignore_permissions=True)