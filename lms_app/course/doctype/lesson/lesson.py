# Copyright (c) 2025, urtaa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class Lesson(Document):
   def validate(self):
      self.validate_lesson_contents()
      if frappe.db.exists(
         "Lesson",
         {
            "course": self.course,
            "order": self.order,
            "name": ["!=", self.name]
         }
      ):
         frappe.throw("Дарааллын тоо давхардаж болохгүй.")
   
   def before_save(self):
      self.send_notification()
	
   def on_update(self):
      self.serialize_lesson_content_order()

   def on_trash(self):
      self.delete_quiz()
      self.delete_lesson_student()
   
   def after_insert(self):
      enrollments = frappe.db.get_all("Enrollment", {"course": self.course}, ["student"])
      for enrollment in enrollments:
         lesson_student = frappe.get_doc({
            "doctype": "Lesson_student",
            "lesson": self.name,
            "student": enrollment.student
         })
         lesson_student.insert(ignore_permissions=True)
         
   def after_delete(self):
      self.serialize_lesson_order(self.course)
      
   def validate_lesson_contents(self):
      if self.lesson_content:
         for idx, row in enumerate(self.lesson_content, start=1):
            content_type = row.content_type

            if content_type == "Video" and not row.video_url:
               frappe.throw(f"Мөр {idx}: Видео URL оруулаагүй байна.")

            elif content_type == "Text" and not row.text_content:
               frappe.throw(f"Мөр {idx}: Текст контент оруулаагүй байна.")

            elif content_type == "File" and not row.attachment:
               frappe.throw(f"Мөр {idx}: Файл оруулаагүй байна.")

            elif content_type == "Link" and not row.external_link:
               frappe.throw(f"Мөр {idx}: URL оруулаагүй байна.")

            elif content_type not in ["Video", "Text", "File", "Link"]:
               frappe.throw(f"Мөр {idx}: Боломжгүй контентын төрөл байна.")

   def serialize_lesson_order(self, course):
      lessons = frappe.get_all(
         "Lesson",
         filters={"course": course},
         fields=["name"],
         order_by="order asc, modified asc"
      )

      for index, lesson in enumerate(lessons, start=1):
         frappe.db.set_value("Lesson", lesson.name, "order", index)
   
   def serialize_lesson_content_order(self):
      contents = self.lesson_content

      for index, content in enumerate(contents, start=1):
         frappe.db.set_value("Lesson_content", content.name, "order", index)
         
   def delete_quiz(self):
      frappe.delete_doc("Quiz", {"lesson": self.name}, force=1)
      
   def delete_lesson_student(self):
      lesson_student = frappe.get_doc("Lesson_student", {"lesson": self.name})
      lesson_student.delete(ignore_permissions=True)

   def send_notification(self):
      enrolled_students = frappe.get_all("Enrollment", filters={"course": self.course}, fields=["student"])
      course_title, instructor_name = frappe.get_value("Course", {"name": self.course}, ["course_title", "instructor"])
      instructor = frappe.get_value("User", {"name": instructor_name}, "full_name")
      if self.is_new():
         for student in enrolled_students:
            notification = frappe.get_doc({
               "doctype": "Notification Log",
               "subject": f"{instructor}",
               "email_content": f"{course_title} сургалтанд {self.lesson_title} хичээл нэмэгдэж орлоо.",
               "type": "Alert",
               "for_user": student["student"],
               "from_user": instructor_name,
               "read": 0
            })
            notification.insert(ignore_permissions=True)
            frappe.publish_realtime(f"notification_{student["student"]}",
               message={"text": f"{course_title} сургалтанд {self.lesson_title} хичээл нэмэгдэж орлоо."}
            )
      else:
         for student in enrolled_students:
            notification = frappe.get_doc({
               "doctype": "Notification Log",
               "subject": f"{instructor}",
               "email_content": f"{course_title} сургалтын {self.lesson_title} хичээлд өөрчлөлт орлоо.",
               "type": "Alert",
               "for_user": student["student"],
               "from_user": instructor_name,
               "read": 0
            })
            notification.insert(ignore_permissions=True)
            frappe.publish_realtime(f"notification_{student["student"]}",
               message={"text": f"{course_title} сургалтын {self.lesson_title} хичээлд өөрчлөлт орлоо."}
            )