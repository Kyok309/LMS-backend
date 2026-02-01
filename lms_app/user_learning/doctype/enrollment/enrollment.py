# Copyright (c) 2025, urtaa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from lms_app.api.certificate import generate_certificate_pdf

class Enrollment(Document):
	def after_insert(self):
		self.create_lesson_students()
		self.send_notification()
	
	def on_update(self):
		if self.completion_status == "Finished":
			generate_certificate_pdf(self.name)
			self.db_set("certificate_issued", 1)
	
	def create_lesson_students(self):
		lessons = frappe.get_all("Lesson", filters={"course": self.course}, fields=["name"])
		for lesson in lessons:
			lesson_student = frappe.get_doc({
				"doctype": "Lesson_student",
				"lesson": lesson["name"],
				"student": self.student
			})
			lesson_student.insert(ignore_permissions=True)

	def send_notification(self):
		instructor, course_title = frappe.get_value("Course", self.course, ["instructor", "course_title"])
		student_full_name = frappe.get_value("User", self.student, "full_name")

		notification = frappe.get_doc({
			"doctype": "Notification Log",
			"subject": f"{course_title}",
			"email_content": f"{course_title} сургалтанд {student_full_name} суралцагч нэмэгдэж элслээ.",
			"type": "Alert",
			"for_user": instructor,
			"from_user": self.student,
			"read": 0
		})
		notification.insert(ignore_permissions=True)
		
		frappe.publish_realtime(
			f"notification_{instructor}",
			message={"text": f"{course_title} сургалтанд {student_full_name} суралцагч нэмэгдэж элслээ."}
		)