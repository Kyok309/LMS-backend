import frappe
import pdfkit
import os
from jinja2 import Template
from lms_app.utils.utils import response_maker

def generate_certificate_pdf(enrollmentId = None):
   """
   Generate PDF certificate for completed enrollment
   """
   try:
      enrollment = frappe.get_doc('Enrollment', enrollmentId)
      course = frappe.get_doc('Course', enrollment.course)
      student = frappe.get_doc('User', enrollment.student)
      instructor = frappe.get_doc('User', course.instructor)
      
      # Create unique certificate ID
      cert_id = f"CERT-{enrollment.student.split('@')[0]}-{int(__import__('time').time())}"
      
      # Prepare context
      context = {
         'student_name': student.full_name,
         'course_title': course.course_title,
         'completion_date': frappe.utils.formatdate(frappe.utils.today()),
         'instructor_name': instructor.full_name,
         'certificate_id': cert_id,
      }
      
      # Read and render template
      template_path = os.path.join(
         frappe.get_app_path('lms_app'),
         'templates',
         'certificate.html'
      )
      
      with open(template_path, 'r') as f:
         template = Template(f.read())
      
      html_content = template.render(**context)
            
      # Generate PDF
      pdf_bytes = pdfkit.from_string(
         html_content,
         False,   # False = return bytes instead of saving file
         options={
            'page-size': 'A4',
            'orientation': 'Landscape',
            'margin-top': '0',
            'margin-right': '0',
            'margin-bottom': '0',
            'margin-left': '0',
         }
      )

      file = frappe.get_doc({
         "doctype": "File",
         "file_name": f"{cert_id}.pdf",
         "content": pdf_bytes,
         "is_private": 1,
         "attached_to_doctype": "Certificate",
         "attached_to_name": cert_id
      })
      file.insert(ignore_permissions=True)
      # Create certificate record
      certificate = frappe.get_doc({
         'doctype': 'Certificate',
         'name': cert_id,
         'course': enrollment.course,
         'student': enrollment.student,
         'enrollment': enrollment.name,
         'file': file.file_url
      })
      certificate.insert(ignore_permissions=True)
      frappe.db.commit()
      
      return certificate
      
   except Exception as e:
      frappe.log_error(str(e), 'Certificate Generation Error')
      print(str(e))
      raise
    
@frappe.whitelist(methods=["GET"])
def get_certificate(courseId = None):
   user = frappe.session.user
   if not courseId:
      response_maker(
         desc="Сургалтын ID байхгүй байна.",
         status=400,
         type="error"
      )
   if not frappe.db.exists("Has Role", {"parent": user, "role": "Student"}):
      response_maker(
         desc="Сертификатын мэдээлэл авах эрхгүй хэрэглэгч байна.",
         status=403,
         type="error"
      )
   try:
      certificate=frappe.get_doc("Certificate", {"course": courseId, "student": user})
      response_maker(
         desc="Сертификат амжилттай авлаа.",
         data=certificate
      )
   except frappe.DoesNotExistError:
      response_maker(
         desc="Сертификат олдсонгүй.",
         status=404,
         type="error"
      )
   except:
      frappe.log_error(frappe.get_traceback(), "Get certificate error")
      print(frappe.get_traceback())
      response_maker(
         desc="Сертификат авахад алдаа гарлаа.",
         status=500,
         type="eror"
      )

@frappe.whitelist(methods=["GET"])
def get_certificate_file(certificateId = None):
   try:
      user = frappe.session.user
      certificate = frappe.get_doc("Certificate", certificateId)
      if certificate.student == user:
         file = frappe.get_doc("File", {"attached_to_name": certificateId})
         frappe.local.response.filename = file.file_name
         frappe.local.response.filecontent = file.get_content()
         frappe.local.response.type = "download"
         response_maker(
            desc="Сертификатийн файл амжилттай авлаа."
         )
   except frappe.DoesNotExistError:
      response_maker(
         desc="Сертификат олдсонгүй.",
         status=404,
         type="error"
      )
   except:
      response_maker(
         desc="Сертификатийн файл авахад алдаа гарлаа.",
         status=500,
         type="error"
      )