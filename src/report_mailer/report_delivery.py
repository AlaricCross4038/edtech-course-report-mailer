from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .infrai_email import EmailResult, InfraiEmail


@dataclass(frozen=True)
class Learner:
    name: str
    email: str
    deadline: date
    completed: bool


@dataclass(frozen=True)
class CourseReport:
    course: str
    educator_email: str
    learners: tuple[Learner, ...]


def overdue_learners(report: CourseReport, today: date) -> tuple[Learner, ...]:
    return tuple(
        learner
        for learner in report.learners
        if not learner.completed and learner.deadline < today
    )


def format_report(report: CourseReport, today: date) -> str:
    overdue = overdue_learners(report, today)
    lines = [f"Course report: {report.course}", f"As of: {today.isoformat()}", ""]
    if overdue:
        lines.append("Learners past deadline:")
        lines.extend(f"- {learner.name} ({learner.email})" for learner in overdue)
    else:
        lines.append("No learners are past the deadline.")
    return "\n".join(lines)


def make_pdf(text: str) -> bytes:
    """Build a one-page text PDF for the email attachment."""
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 11 Tf 54 740 Td ({escaped}) Tj ET".encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    output.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    output.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(output)


def send_course_report(client: InfraiEmail, report: CourseReport, today: date) -> EmailResult:
    body = format_report(report, today)
    pdf = make_pdf(body)
    attachment_note = f"\n\nPDF attachment bytes: {len(pdf)}"
    # The application boundary is the same concise InfraiEmail().send idiom.
    return client.send(
        to=[report.educator_email],
        subject=f"{report.course} learner report",
        body=body + attachment_note,
        request_id=f"course-report-{report.course}-{today.isoformat()}",
    )
