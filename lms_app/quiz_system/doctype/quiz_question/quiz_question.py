# Copyright (c) 2025, urtaa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from lms_app.utils.utils import update_quiz_total_score_after_commit
import frappe


class Quiz_question(Document):
	def validate(self):
		if frappe.db.exists(
			"Quiz_question",
			{
				"quiz": self.quiz,
				"order": self.order,
				"name": ["!=", self.name]
			}
		):
			frappe.throw("Дарааллын тоо давхардаж болохгүй.")
   
	def serialize_question_order(self, quiz):
		questions = frappe.get_all(
			"Quiz_question",
			filters={"quiz": quiz},
			fields=["name"],
			order_by="`order` asc, modified asc"
		)

		for index, question in enumerate(questions, start=1):
			frappe.db.set_value("Quiz_question", question.name, "order", index)
   
	def after_insert(self):
		update_quiz_total_score_after_commit(self.quiz)
		self.serialize_question_order(self.quiz)

	def on_update(self):
		update_quiz_total_score_after_commit(self.quiz)
		self.serialize_question_order(self.quiz)

	def after_delete(self):
		update_quiz_total_score_after_commit(self.quiz)
		self.serialize_question_order(self.quiz)