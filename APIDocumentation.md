## LMS API гарын авлага (Backend)

Энэ баримт нь LMS backend-ийн **бүх гол API endpoint-уудыг** frontend баримт шиг хэлбэрээр нэг дор эмхэтгэж өгнө.

- **Protocol**: HTTPS (зөвлөмж)
- **Format**: Бүх хариу `JSON` (`response_maker` ашигладаг)
- **Base URL**:

```text
BASE_URL = https://api.example.com
BACKEND  = {BASE_URL}/api/method/lms   // эсвэл таны суулгалтад тохирсон app name
Жишээ:   https://api.example.com/api/method/lms.auth.login
```

Доорх бүх endpoint-ууд:

```text
{BACKEND}.{resource}.{method}
жишээ: {BACKEND}.auth.login
```

---

## Аюулгүй байдал, Authentication

- **Хамгаалагдсан endpoint-ууд** `frappe.session.user`-ийг ашигладаг.
- Frontend талд **Bearer JWT access token**-ийг cookie/session дотор хадгалдаг (NextAuth).
- Хүсэлтэнд:

```http
Authorization: Bearer <ACCESS_TOKEN>
Accept: application/json
Content-Type: application/json
```

Жич: `allow_guest=True` байгаа endpoint-ууд дээр authentication заавал биш.

---

## 1. Нэвтрэлт ба хэрэглэгчийн эрх (`auth`)

### 1.1 Бүртгүүлэх

#### Endpoint

```text
POST {BACKEND}.auth.signup
```

#### Тайлбар

`User` + `Student_profile` эсвэл `Instructor_profile` үүсгэнэ.

#### Body (JSON)

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "99119911",
  "password": "pass1234",
  "role": "Student"   // эсвэл "Instructor"
}
```

#### Хариу

- `201` – Амжилттай
- `409` – Ижил рольтой хэрэглэгч бүртгэлтэй
- `400/500` – Алдаа (`desc` талбарт тайлбарлана)

---

### 1.2 Нэвтрэх

#### Endpoint

```text
POST {BACKEND}.auth.login
```

#### Тайлбар

Frappe OAuth2 `password` flow ашиглаж **access_token / refresh_token** авна.

#### Body (x-www-form-urlencoded)

Backend дотор:

- `grant_type=password`
- `client_id`, `client_secret` – `OAuth Client` doc-оос
- `username=email`, `password=password`

Frontend талаас:

```json
{
  "email": "user@example.com",
  "password": "pass1234"
}
```

#### Амжилттай хариу (гол талбарууд)

```json
{
  "responseType": "ok",
  "data": {
    "access_token": "<ACCESS_TOKEN>",
    "refresh_token": "<REFRESH_TOKEN>",
    "expires_in": 900,
    "roles": ["Student", "Instructor"],
    "user": {
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "99119911",
      "user_image": "/files/avatar.png"
    }
  }
}
```

---

### 1.3 Нууц үг солих (логин хийсэн хэрэглэгч)

#### Endpoint

```text
POST {BACKEND}.auth.change_password
```

#### Params (form/query)

```text
old_password=<OLD>&new_password=<NEW>
```

#### Тайлбар

- `frappe.session.user`-ийн хуучин нууц үгийг шалгаад шинэ нууц үг болгоно.
- Алдаа тохиолдолд:
  - `403` – Guest эсвэл эрхгүй
  - `400` – Хуучин нууц үг буруу, эсвэл шинэ нь хуучинтай ижил

---

### 1.4 Нэвтэрсэн хэрэглэгчийн мэдээлэл

#### Endpoint

```text
GET {BACKEND}.auth.get_me
```

#### Тайлбар

`Student` эсвэл `Instructor` рольтой нэвтэрсэн хэрэглэгчийн үндсэн мэдээлэл.

#### Хариу (жишээ)

```json
{
  "responseType": "ok",
  "data": {
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "user_image": "/files/avatar.png",
    "email": "user@example.com"
  }
}
```

---

## 2. Суралцагчийн профайл (`student`)

### 2.1 Профайл авах

#### Endpoint

```text
GET {BACKEND}.student.get_student_profile
```

#### Тайлбар

`Student_profile` + `User` мэдээллийг нэгтгэнэ.

#### Хариу (гол талбарууд)

```json
{
  "data": {
    "school": "NUM",
    "education_level": "Bachelor",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "99119911",
    "profile": "/files/profile.jpg"
  }
}
```

---

### 2.2 Профайл шинэчлэх

#### Endpoint

```text
PUT {BACKEND}.student.update_student_profile
```

#### Body (JSON)

```json
{
  "school": "MUST",
  "education_level": "Masters",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "99119911",
  "user_image": "/files/profile.jpg"
}
```

`Student_profile` болон `User` doc дээр давхар бичнэ.

---

## 3. Багшийн профайл (`instructor`)

### 3.1 Багшийн профайл авах (public/guest зөвшөөрсөн)

#### Endpoint

```text
GET {BACKEND}.instructor.get_instructor_profile?instructorId=<USER_ID>
```

#### Хариу (гол талбарууд)

- `Instructor_profile`-ийн: `profession`, `expertise`, `qualification`, `experience`, `total_courses`, `rating`
- `User`-ийн: `first_name`, `last_name`, `email`, `phone`, `user_image`, `bio`

---

### 3.2 Багшийн профайл шинэчлэх

#### Endpoint

```text
PUT {BACKEND}.instructor.update_instructor_profile
```

#### Body (JSON)

`Instructor_profile` + `User` дээрх аль ч талбарыг илгээж болно (нэр `name`-г өөрчилдөггүй).

---

## 4. Хяналтын самбар (`dashboard`)

### 4.1 Суралцагчийн dashboard

#### Endpoint

```text
GET {BACKEND}.dashboard.get_dashboard
```

#### Гол талбарууд

- `enrolled_courses`, `finished_lessons`, `finished_courses`
- `average_score`, `completion_rate`
- `completed_lesson_week[]` – 7 хоног бүрийн гүйцэтгэл
- `course_category[]` – ангилал тус бүрийн сургалтын тоо
- `progress_category[]` – ангилал тус бүрийн дундаж явц
- `avg_course[]` – курс тус бүрийн дундаж оноо

---

### 4.2 Багшийн dashboard

#### Endpoint

```text
GET {BACKEND}.dashboard.get_dashboard_instructor
```

#### Гол талбарууд

- `total_enrollments[]` – курс тус бүрийн элсэлт
- `total_revenue[]` – курс тус бүрийн орлого
- `total_lessons[]` – курс тус бүрийн хичээл
- `average_score_course[]` – курс тус бүрийн дундаж оноо
- `enrollment_month[]` – сүүлийн 6 сарын элсэлт
- `completion_rate[]` – курсийн completion rate

---

## 5. Сургалт (`course`) ба ангилал (`category`)

### 5.1 Ангиллын жагсаалт (public)

#### Endpoint

```text
GET {BACKEND}.category.get_categories
```

---

### 5.2 Нийт сургалтууд (public listing)

#### Endpoint

```text
GET {BACKEND}.course.get_courses
```

#### Query параметрүүд

- `categories` – `name` жагсаалт, comma-separated (`cat1,cat2`)
- `min_price`, `max_price` (int)
- `sort_by` – жишээ: `creation_desc`, `price_asc`
- `page` (int, default 1)
- `search` – course title / description / instructor name
- `level` – `Beginner`, `Intermediate`, `Advanced` гэх мэт

Хариуд:

- `courses[]` – курс бүрийн үндсэн мэдээлэл + `instructor_full_name`, `instructor_image`, `category_name`, `student_count`, `lesson_count`
- `page`, `per_page`, `total_count`, `total_pages`

---

### 5.3 Нэг сургалтын дэлгэрэнгүй (public)

#### Endpoint

```text
GET {BACKEND}.course.get_course?courseId=<COURSE_ID>
```

#### Гол талбарууд

- Course info: `course_title`, `description`, `learning_curve`, `requirement`, `price`, `level`, `rating`, `thumbnail`, `published_on`
- `instructor_name`, `instructor_image`
- `category_name`
- `total_students`
- `is_enrolled` – нэвтэрсэн хэрэглэгч уг курсэд элссэн эсэх

---

### 5.4 Багшийн сургалтуудын жагсаалт

#### Endpoint

```text
GET {BACKEND}.course.get_courses_instructor
```

#### Query

- `level`, `category`, `status` (`All` by default)
- `sort_by`, `search`, `page`

---

### 5.5 Нэг сургалт (Instructor view)

#### Endpoint

```text
GET {BACKEND}.course.get_course_instructor?id=<COURSE_ID>
```

Зөвхөн тухайн курсийн багш нэвтэрсэн үед.

---

### 5.6 Сургалт үүсгэх

#### Endpoint

```text
POST {BACKEND}.course.create_course
```

#### Body (JSON)

```json
{
  "instructor": "instructor@example.com",
  "course_title": "React Basics",
  "category": "CATEGORY-ID",
  "level": "Beginner",
  "thumbnail": "/files/thumbnail.jpg",
  "description": "...",
  "introduction": "...",
  "learning_curve": "...",
  "requirement": "...",
  "price_type": "Paid",
  "price": 100000
}
```

---

### 5.7 Сургалт засах

#### Endpoint

```text
PUT {BACKEND}.course.update_course
```

#### Body (JSON)

```json
{
  "courseId": "COURSE-ID",
  "course_title": "New title",
  "category": "CATEGORY-ID",
  "level": "Intermediate",
  "thumbnail": "...",
  "description": "...",
  "introduction": "...",
  "learning_curve": "...",
  "requirement": "...",
  "price_type": "Paid",
  "price": 120000,
  "status": "Draft"
}
```

---

### 5.8 Сургалт устгах

#### Endpoint

```text
DELETE {BACKEND}.course.delete_course?courseId=<COURSE_ID>
```

- Хэрвээ уг курсэд `Enrollment` байвал устгах боломжгүй (`400`).

---

## 6. Хичээл (`lesson`)

### 6.1 Суралцагчийн хичээлийн жагсаалт

#### Endpoint

```text
GET {BACKEND}.lesson.get_lessons?courseId=<COURSE_ID>
```

`Enrollment` шалгана.

---

### 6.2 Нэг хичээл (Student view)

#### Endpoint

```text
GET {BACKEND}.lesson.get_lesson?courseId=<COURSE_ID>&lessonId=<LESSON_ID>
```

Хариудад:

- `Lesson`-ийн бүх талбар
- `course_title`, `instructor`-ийн нэр, зураг
- `lesson_content` – `order`-оор эрэмбэлсэн

---

### 6.3 Хичээлийн жагсаалт (Instructor view)

#### Endpoint

```text
GET {BACKEND}.lesson.get_lessons_instructor?courseId=<COURSE_ID>
```

---

### 6.4 Нэг хичээл (Instructor view)

#### Endpoint

```text
GET {BACKEND}.lesson.get_lesson_instructor?lessonId=<LESSON_ID>
```

---

### 6.5 Хичээл үүсгэх

#### Endpoint

```text
POST {BACKEND}.lesson.create_lesson
```

#### Params (form/query эсвэл JSON)

- `lesson_title` (required)
- `order` (required, int)
- `course` (required, course id)
- `description` (optional)
- `lesson_content` (optional, child table JSON)

---

### 6.6 Хичээл засах

#### Endpoint

```text
PUT {BACKEND}.lesson.update_lesson
```

#### Body (JSON)

```json
{
  "name": "LESSON-ID",
  "lesson_title": "New title",
  "description": "...",
  "lesson_content": [ /* child rows */ ]
}
```

---

### 6.7 Хичээлүүдийн дараалал өөрчлөх

#### Endpoint

```text
PUT {BACKEND}.lesson.update_lessons_order
```

#### Body (JSON)

```json
{
  "lessons": [
    { "name": "LESSON-1", "order": 1 },
    { "name": "LESSON-2", "order": 2 }
  ]
}
```

---

### 6.8 Хичээл устгах

#### Endpoint

```text
DELETE {BACKEND}.lesson.delete_lesson?lessonId=<LESSON_ID>
```

---

### 6.9 Хичээлийн private файл авах

#### Endpoint

```text
POST {BACKEND}.lesson.get_lesson_file
```

#### Params

- `lesson_id`
- `file_url`

Зөвхөн тухайн курсэд элссэн суралцагчдад private `File`-ийг stream хийнэ (download).

---

## 7. Элсэлт (`enrollment`) ба сертификат (`certificate`)

### 7.1 Элсэлт шалгах (route хамгаалалт)

#### Endpoint

```text
GET {BACKEND}.enrollment.check_enrollment_api?courseId=<COURSE_ID>
```

Хариу:

```json
{ "data": { "enrolled": true } }
```

---

### 7.2 Суралцагчийн бүх элсэлт

#### Endpoint

```text
GET {BACKEND}.enrollment.get_enrollments_student
```

Хариу – `Enrollment` + `Course`-ийн нийлмэл жагсаалт.

---

### 7.3 Элсэлт үүсгэх (үнэгүй курс)

#### Endpoint

```text
POST {BACKEND}.enrollment.create_enrollment?courseId=<COURSE_ID>
```

- Зөвхөн үнэ `0`-тэй курс дээр шууд `Enrollment` үүсгэнэ.
- Төлбөртэй курс дээр Stripe webhook-оор үүсдэг (доор).

---

### 7.4 Сертификат авах

#### Endpoint

```text
GET {BACKEND}.certificate.get_certificate?courseId=<COURSE_ID>
```

Хариу:

- `Certificate` doc (course, student, enrollment, `file` – pdf file_url гэх мэт)

---

### 7.5 Сертификатын PDF татах

#### Endpoint

```text
GET {BACKEND}.certificate.get_certificate_file?certificateId=<CERTIFICATE_ID>
```

- `File` doc-оос PDF-ийг `download` болгон stream хийнэ (response type `download`).

---

## 8. Шалгалт (`quiz`) ба асуултууд (`quiz_question`), submission (`submission`)

### 8.1 Шалгалтын үндсэн мэдээлэл (Student view)

#### Endpoint

```text
GET {BACKEND}.quiz.get_quiz?quizId=<QUIZ_ID>&courseId=<COURSE_ID>
```

`Enrollment`-ийг шалгана.

---

### 8.2 Шалгалтын жагсаалт (Student view – нэг хичээлийн)

#### Endpoint

```text
GET {BACKEND}.quiz.get_quizzes?lessonId=<LESSON_ID>
```

---

### 8.3 Шалгалтын жагсаалт (Instructor view)

#### Endpoint

```text
GET {BACKEND}.quiz.get_quizzes_instructor?lessonId=<LESSON_ID>
```

---

### 8.4 Нэг шалгалт (Instructor view, асуулттай нь)

#### Endpoint

```text
GET {BACKEND}.quiz.get_quiz_instructor?quizId=<QUIZ_ID>
```

Хариу:

- `Quiz` info + `quiz_questions[]` (basic fields)

---

### 8.5 Шалгалт үүсгэх

#### Endpoint

```text
POST {BACKEND}.quiz.create_quiz
```

#### Params

- `lesson` (required)
- `title` (required)
- `description` (optional)
- `passing_score` (optional)
- `time_limit_minutes` (required)

---

### 8.6 Шалгалт засах

#### Endpoint

```text
PUT {BACKEND}.quiz.update_quiz
```

#### Params

- `quizId` (required)
- `title`, `description`, `passing_score`, `time_limit_minutes` (required)

---

### 8.7 Шалгалт устгах

#### Endpoint

```text
DELETE {BACKEND}.quiz.delete_quiz?quizId=<QUIZ_ID>
```

---

### 8.8 Шалгалтын асуултууд (Student view)

#### Endpoint

```text
GET {BACKEND}.quiz_question.get_quiz_questions?quizId=<QUIZ_ID>&courseId=<COURSE_ID>
```

- Асуулт бүрийн **хариултууд random эрэмбэтэй** `quiz_question_answer[]` буцаана.
- Зөвхөн уг курсэд элссэн суралцагчид.

---

### 8.9 Шалгалтын асуултууд (Instructor view, list)

#### Endpoint

```text
GET {BACKEND}.quiz_question.get_quiz_questions_instructor?quizId=<QUIZ_ID>
```

---

### 8.10 Нэг асуулт (Instructor view)

#### Endpoint

```text
GET {BACKEND}.quiz_question.get_quiz_question_instructor?quizId=<QUIZ_ID>&questionId=<QUESTION_ID>
```

---

### 8.11 Асуулт үүсгэх

#### Endpoint

```text
POST {BACKEND}.quiz_question.create_quiz_question
```

#### Params

- `quizId`, `question_text`, `order`, `score` (required)
- `question_file` (optional)
- `quiz_question_answer[]` – child rows (answer_text, is_correct г.м.)

---

### 8.12 Асуулт засах

#### Endpoint

```text
PUT {BACKEND}.quiz_question.update_quiz_question
```

#### Params

- `questionId`, `quiz`, `question_text`, `order`, `score` (required)
- `question_file`, `quiz_question_answer` (optional)

---

### 8.13 Асуулт устгах

#### Endpoint

```text
DELETE {BACKEND}.quiz_question.delete_quiz_question?questionId=<QUESTION_ID>
```

---

### 8.14 Шалгалтын submission-уудын жагсаалт

#### Endpoint

```text
GET {BACKEND}.submission.get_quiz_submissions?quizId=<QUIZ_ID>&courseId=<COURSE_ID>
```

- `Quiz_submission[]` – score, passed, score_percent, creation

---

### 8.15 Шинэ submission үүсгэх

#### Endpoint

```text
POST {BACKEND}.submission.create_quiz_submission
```

#### Params

- `quizId` (required)
- `courseId` (required)
- `student_answers` (required; массив) – жишээ:

```json
[
  {
    "quiz_question": "QUESTION-ID-1",
    "quiz_question_answer": "ANSWER-ID-1"
  }
]
```

Backend:

- Зөв хариултыг `Quiz_question_answer`-аас олж шалгана.
- `score`, `score_percent`, `passed` тооцоод `Quiz_submission` үүсгэнэ.

---

## 9. Төлбөр ба Stripe (`payment`, `stripe`)

### 9.1 Stripe onboarding link (Instructor)

#### Endpoint

```text
POST {BACKEND}.stripe.create_onboarding_link
```

Хариу:

- `data.url` – Stripe Account onboarding URL

---

### 9.2 Checkout session үүсгэх (Student)

#### Endpoint

```text
POST {BACKEND}.stripe.create_checkout_session
```

#### Params

- `course_id` (required, form/query)

Хариу:

- `data.session_url` – Stripe checkout URL

---

### 9.3 Stripe webhook (server-to-server)

#### Endpoint

```text
POST {BACKEND}.stripe.stripe_webhook
```

- `allow_guest=True`
- Stripe-аас ирсэн `checkout.session.completed` дээр:
  - `Payment` doc үүсгэнэ
  - `Enrollment` doc үүсгэнэ
  - `frappe.db.commit()` хийнэ

---

### 9.4 Stripe account status (Instructor)

#### Endpoint

```text
GET {BACKEND}.stripe.get_stripe_account_status
```

Хариу:

- `charges_enabled`
- `account_id`

---

### 9.5 Суралцагчийн төлбөрүүд

#### Endpoint

```text
GET {BACKEND}.payment.get_payments_student
```

Хариу:

- `payments[]` – course, amount, payment_status, payment_method, paid_on, `course_title`
- `total_paid_amount`

---

### 9.6 Багшийн төлбөрүүд

#### Endpoint

```text
GET {BACKEND}.payment.get_payments_instructor
```

Хариу:

- `payments[]` – сургалт, суралцагчийн нэр/имэйл + төлбөрийн мэдээлэл
- `total_paid_amount`

---

## 10. Үнэлгээ (Reviews) (`review`)

### 10.1 Нэг сургалтын үнэлгээнүүд

#### Endpoint

```text
GET {BACKEND}.review.get_reviews_course?courseId=<COURSE_ID>
```

---

### 10.2 Багшийн үнэлгээнүүд

#### Endpoint

```text
GET {BACKEND}.review.get_reviews_instructor?instructorId=<INSTRUCTOR_USER_ID>
```

---

### 10.3 Үнэлгээ үүсгэх

#### Endpoint

```text
POST {BACKEND}.review.create_review
```

#### Params

- `courseId` (required, enrolled байх ёстой)
- `rating` (1–5, required)
- `reviewText` (optional)

---

## 11. Мэдэгдэл (`notification`)

### 11.1 Мэдэгдлүүдийн жагсаалт

#### Endpoint

```text
GET {BACKEND}.notification.get_notifications
```

`Notification Log`-оос тухайн хэрэглэгчийн мэдэгдлүүдийг буцаана.

---

### 11.2 Мэдэгдлийг уншсанаар тэмдэглэх

#### Endpoint

```text
PUT {BACKEND}.notification.read_notification?notifId=<NOTIF_ID>
```

---

## 12. Тайлан (Instructor report) (`report`)

### 12.1 Багшийн тайлан

#### Endpoint

```text
GET {BACKEND}.report.get_report_instructor
```

Хариу:

- Курс тус бүрийн:
  - `course_title`, `published_on`, `status`, `price_type`, `price`, `workflow_state`
  - `enrollments` – элсэлтийн тоо
  - `total_revenue` – нийт орлого

---