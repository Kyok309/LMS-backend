# Copyright (c) 2025, urtaa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe


class Review(Document):
	def calculate_average_rating(self):
		course = frappe.get_doc("Course", self.course)
		reviews = frappe.get_all(
			"Review",
			filters={"course": self.course},
			fields=["rating"]
		)
		if reviews:
			total_rating = sum([review.rating for review in reviews])
			average_rating = total_rating / len(reviews)
			course.rating = average_rating
			course.save(ignore_permissions=True)

	def calculate_instructor_rating(self):
		course_instructor = frappe.get_value("Course", self.course, "instructor")
		instructor_profile = frappe.get_doc("Instructor_profile", {"user": course_instructor})
		courses = frappe.get_all(
			"Course",
			filters={"instructor": course_instructor, "rating": ["!=", 0]},
			fields=["rating"]
		)
		
		if courses:
			total_rating = sum([course.rating for course in courses])
			average_rating = total_rating / len(courses)
			instructor_profile.rating = average_rating
			instructor_profile.save(ignore_permissions=True)

	def validate(self):
		if self.rating < 1 or self.rating > 5:
			frappe.throw("Үнэлгээ 1-ээс 5 хооронд байх ёстой.")

	def after_delete(self):
		self.calculate_average_rating()
		self.calculate_instructor_rating()

	def on_update(self):
		self.calculate_average_rating()
		self.calculate_instructor_rating()

	def after_insert(self):
		self.calculate_average_rating()
		self.calculate_instructor_rating()
