from typing import List
from fastapi import APIRouter, HTTPException
from utils import announcement
from mongo_ops import announcement_data
from pydantic_models.announcement_model import Announcement, AnnouncementAddRequest


router = APIRouter(
    tags=["Announcement"]
)


@router.post("/announcement")
def add_announcement_data(request: AnnouncementAddRequest):
    try:
        announcement.add_announcement(
            announcement_config=request.data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/announcement/{grade}")
def get_announcements_based_on_grade(grade: str) -> List[Announcement]:
    try:
        return announcement_data.get_all_announcement_for_grade(
            grade=grade
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))