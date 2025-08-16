from datetime import datetime, timezone, date
from mongo_ops.instructor_data import get_instructor_data_by_email_id
from pydantic_models.announcement_model import AnnouncementSpec, Announcement
from mongo_ops import announcement_data


def add_announcement(announcement_config: AnnouncementSpec):
    try:
        instructor = get_instructor_data_by_email_id(announcement_config.poster_email)
        announcement_id = f"{datetime.now(timezone.utc):%Y%m%d%H%M%S}:{instructor.instructor_id}"
        announcement = Announcement(
            announcement_id=announcement_id,
            grade=str(announcement_config.grade),
            title=announcement_config.title,
            poster_email=announcement_config.poster_email,
            content=announcement_config.content,
            event_date=announcement_config.event_date,
            posting_date=date.today().isoformat()
        )
        announcement_data.add_announcement(announcement)
        return announcement_id
    except Exception as e:
        print(e)
        raise e
