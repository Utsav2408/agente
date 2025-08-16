from typing import List
from pymongo.collection import Collection

from config.mongo_connect import mongo
from constant.constant import ANNOUNCEMENT_COLLECTION, ANNOUNCEMENT_DB
from mongo_ops.utils import _to_doc
from pydantic_models.announcement_model import Announcement, AnnouncementDetails


# ---------------------------------------------------------------------------
# Mongo connection (opened once, reused)
# ---------------------------------------------------------------------------
_announcement_col: Collection = mongo.get_connection()[ANNOUNCEMENT_DB][ANNOUNCEMENT_COLLECTION]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def add_announcement(announcement: Announcement):
    _announcement_col.insert_one(_to_doc(announcement))


def get_announcement_by_id(announcement_id: str) -> Announcement:
    doc = _announcement_col.find_one({"announcement_id": announcement_id})
    if not doc:
        raise ValueError(f"Announcement with id '{announcement_id}' not found.")
    # Remove MongoDB internal fields if present
    doc.pop("_id", None)
    return Announcement(**doc)

def get_all_announcement_for_poster(poster_email: str) -> List[AnnouncementDetails]:
    cursor = _announcement_col.find({"poster_email": poster_email})
    announcements: List[AnnouncementDetails] = []
    for doc in cursor:
        doc.pop("_id", None)
        announcements.append(AnnouncementDetails(**doc))
    return announcements


def get_all_announcement_for_grade(grade: str) -> List[Announcement]:
    cursor = _announcement_col.find({"grade": grade})
    announcements: List[Announcement] = []
    for doc in cursor:
        doc.pop("_id", None)
        announcements.append(Announcement(**doc))
    return announcements