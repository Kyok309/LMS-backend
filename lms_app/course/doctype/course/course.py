# Copyright (c) 2025, urtaa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class Course(Document):
    def after_insert(self):
        self.update_course_count()

    def on_trash(self):
        self.delete_lessons()
    
    def after_delete(self):
        self.update_course_count()

    def before_save(self):
        if self.status == "Published":
            self.published_on = frappe.utils.nowdate()
        
    def on_update(self):
        print("Notif about to publish")
        frappe.publish_realtime("notification",
            message={"text": "djks"}
        )
        frappe.db.commit() 
        print("Notif published")
    def validate(self):
        if not frappe.db.exists("Lesson", {"course": self.name}):
            self.status = "Draft"
        if self.price_type == "Free":
            self.price = 0

    def update_course_count(self):
        total = frappe.db.count("Course", {"instructor": self.instructor})
        user = frappe.db.get_value("Instructor_profile", {"user": self.instructor}, "name")
        frappe.db.set_value("Instructor_profile", user, "total_courses", total)
        
    def delete_lessons(self):
        lessons = frappe.get_all(
            "Lesson",
            filters={"course": self.name},
            pluck="name"
        )

        for lesson in lessons:
            frappe.delete_doc("Lesson", lesson, force=1)