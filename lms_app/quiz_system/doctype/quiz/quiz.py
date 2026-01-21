# Copyright (c) 2025, urtaa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe


class Quiz(Document):
	def on_trash(self):
		self.delete_quiz_questions()

	def delete_quiz_questions(self):
		questions = frappe.get_all(
			"Quiz Question",
			filters={"quiz": self.name},
			pluck="name"
		)

		for question in questions:
			frappe.delete_doc("Quiz Question", question, force=1)