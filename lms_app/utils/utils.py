import frappe

def response_maker(desc="success", status=200, type="ok", data=None, meta=None):
    try:
        frappe.response["desc"] = desc
        frappe.response["http_status_code"] = status
        frappe.response["responseCode"] = status
        frappe.response["responseType"] = type
        
        if data:
            frappe.response["data"] = data
        else:
            frappe.response["data"] = []
        return
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Response Maker Error")
        frappe.response["desc"] = "Response maker error"
        frappe.response["http_status_code"] = 500
        frappe.response["responseType"] = "error"
        
        frappe.response["data"] = e.with_traceback()
        return
    
def update_quiz_total_score(quiz_name):
    total = frappe.db.sql("""SELECT COALESCE(SUM(score), 0) FROM `tabQuiz_question` WHERE quiz = %s""", (quiz_name,))[0][0]
    print(total)
    frappe.db.set_value("Quiz", quiz_name, "total_score", total)
    frappe.db.commit()
    print(frappe.db.get_value("Quiz", quiz_name, "total_score"))

def update_quiz_total_score_after_commit(quiz_name):
    frappe.db.after_commit.add(
        lambda: update_quiz_total_score(quiz_name)
    )