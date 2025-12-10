# Copyright (c) 2025, urtaa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class Course(Document):
    def before_save(self):
        if self.status == "Published":
            self.published_on = frappe.utils.nowdate()