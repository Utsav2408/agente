from fastapi import APIRouter, HTTPException
from mongo_ops.announcement_data import get_all_announcement_for_poster, get_announcement_by_id
from utils import announcement
from pydantic_models.announcement_model import AnnouncementData, AnnouncementDetails, AnnouncementID, AnnouncementSpec


router = APIRouter(
    tags=["Announcement"]
)


@router.post(
    path="/instructor/announcement",
    operation_id="create_announcement",
    description="Use this function to create an announcement and store in db"
)
def create_announcement(request: AnnouncementSpec) -> AnnouncementID:
    """
    Use this function to create an announcement and store in db.

    Args:
        request (AnnouncementSpec): The request body containing announcement details.

    Returns:
        AnnouncementID containing the unique identifier of support ticket raised

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        announcement_id = announcement.add_announcement(
            announcement_config=request
        )
        return AnnouncementID(
            announcement_id=announcement_id
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get(
    path="/instructor/{instructor_email}/announcement",
    operation_id="fetch_all_announcements_for_instructor",
    description="Retrieve all active announcements created by instructor",
    response_model=AnnouncementData,
)
def fetch_all_announcements_for_instructor(instructor_email: str) -> AnnouncementData:
    """
    Retrieve all active announcements created by instructor.

    Args:
        instructor_email (str): The email ID of the instructor who created announcement.

    Returns:
        AnnouncementData: A list of announcements raised or created by instructor.

    Raises:
        HTTPException 500: For any unexpected internal errors.
    """
    try:
        announcements = get_all_announcement_for_poster(poster_email=instructor_email)
        return AnnouncementData(
            data=announcements
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    path="/instructor/announcement/{announcement_id}",
    operation_id="fetch_announcement_by_id",
    description="Retrieve a single announcement by its given unique announcement ID",
    response_model=AnnouncementData,
)
def fetch_announcement_by_id(announcement_id: str) -> AnnouncementData:
    """
    Retrieve a single announcement by its given unique announcement ID

    Args:
        announcement_id (str): Unique identifier of the announcement.

    Returns:
        AnnouncementData: A list containing the necessary announcement details.

    Raises:
        HTTPException 500: For any unexpected internal errors.
    """
    try:
        announcement = get_announcement_by_id(announcement_id=announcement_id)
        return AnnouncementData(
            data=[AnnouncementDetails(**announcement.model_dump())]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
