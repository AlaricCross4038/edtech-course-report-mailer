from datetime import date

from report_mailer.report_delivery import CourseReport, Learner, format_report, overdue_learners


def test_report_lists_only_incomplete_learners_past_deadline() -> None:
    today = date(2026, 10, 23)
    report = CourseReport(
        "Editing Lab",
        "teacher@example.com",
        (
            Learner("Late", "late@example.com", date(2026, 10, 22), False),
            Learner("Finished", "finished@example.com", date(2026, 10, 22), True),
            Learner("Upcoming", "upcoming@example.com", date(2026, 10, 25), False),
        ),
    )

    assert [learner.name for learner in overdue_learners(report, today)] == ["Late"]
    assert "Late (late@example.com)" in format_report(report, today)
    assert "Finished" not in format_report(report, today)

