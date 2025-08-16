from datetime import date, datetime, timezone
from pydantic_models.support_ticket_models import SupportTicketSpec, SupportTicketData
from mongo_ops import support_ticket_data, student_data, grade_data


def add_support_ticket(support_ticket_config: SupportTicketSpec):
    try:
        # Fetch student and grade to assign correct ticket assignee
        student = student_data.get_student_public(support_ticket_config.student_id)
        grade = grade_data.get_grade_data(student.grade)

        # Generate unique ticket ID: timestamp (UTC to second precision) + student ID
        ticket_id = f"{datetime.now(timezone.utc):%Y%m%d%H%M%S}:{support_ticket_config.student_id}"

        # Build the support ticket data model
        support_ticket = SupportTicketData(
            support_ticket_id=ticket_id,
            student_id=support_ticket_config.student_id,
            support_type=support_ticket_config.support_type,
            support_summary=support_ticket_config.support_summary,
            support_content=support_ticket_config.support_content,
            created_at=date.today(),
            assignee=grade.grade_head_email_id,
            resolved=False,
            checked=False,
            assignee_reply="",
            suggested_reply=""
        )

        # Persist to Mongo and return the ticket ID
        support_ticket_data.add_support_ticket(support_ticket)
        return ticket_id
    except Exception as e:
        # Bubble up errors for higher-level handling
        raise e
