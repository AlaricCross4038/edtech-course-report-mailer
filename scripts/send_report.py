from datetime import date
import os

from report_mailer.infrai_email import InfraiEmail
from report_mailer.report_delivery import CourseReport, Learner, send_course_report


report = CourseReport(
    course="Intro to Digital Storytelling",
    educator_email=os.environ["REPORT_RECIPIENT"],
    learners=(
        Learner("Mina", "mina@example.com", date(2026, 10, 20), False),
        Learner("Jo", "jo@example.com", date(2026, 10, 30), True),
    ),
)
result = send_course_report(InfraiEmail(), report, date.today())
print(f"sent message {result.message_id}")
