from typing import List
from pymongo.collection import Collection
from bson import ObjectId

from config.mongo_connect import mongo
from constant.constant import COURSE_DB_COLLECTION, ACADEMIC_DB_NAME
from mongo_ops.utils import _to_doc
from pydantic_models.course_models import BookData, CourseData, ChapterData

_course_col: Collection = mongo.get_connection()[ACADEMIC_DB_NAME][COURSE_DB_COLLECTION]


# ---------- helpers ---------------------------------------------------------
def _chapters_differ(a: List[ChapterData], b: List[ChapterData]) -> bool:
    """True if the ordered list of chapter hashes differs."""
    return [c.chapter_hash for c in a] != [c.chapter_hash for c in b]


# ---------- CRUD ------------------------------------------------------------
def insert_course(course: CourseData) -> ObjectId:
    """Insert a new course; returns MongoDB _id."""
    doc = _to_doc(course)
    res = _course_col.insert_one(doc)
    return res.inserted_id


def add_or_update_book(course_id: str, book: BookData) -> bool:
    """
    Add `book` to the course, or replace it if chapters changed.
    Returns True if an update was done, False if nothing changed.
    """
    pipeline_match = {"course_id": course_id, "books.book_id": book.book_id}
    existing = _course_col.find_one(pipeline_match, {"books.$": 1})

    if not existing:
        # No book with same ID – push new book
        _course_col.update_one(
            {"course_id": course_id},
            {"$push": {"books": _to_doc(book)}},
            upsert=False,
        )
        return True

    current_book = BookData.model_validate(existing["books"][0])
    if _chapters_differ(current_book.chapters, book.chapters):
        # Replace the matching sub-document atomically
        _course_col.update_one(
            {"course_id": course_id, "books.book_id": book.book_id},
            {"$set": {"books.$": _to_doc(book)}},
        )
        return True

    return False  # nothing changed


def get_course_by_id(course_id: str) -> CourseData | None:
    doc = _course_col.find_one({"course_id": course_id}, {"_id": 0})
    return CourseData.model_validate(doc) if doc else None


def get_course_by_name(name: str) -> CourseData | None:
    doc = _course_col.find_one({"course_name": name}, {"_id": 0})
    return CourseData.model_validate(doc) if doc else None


def get_books_for_course_and_grade(name: str, grade: str) -> List[BookData]:
    doc = _course_col.find_one({"course_name": name}, {"books": 1, "_id": 0})
    if not doc:
        return []
    return [
        BookData.model_validate(b)
        for b in doc.get("books", [])
        if grade in b.get("grade_ids", [])
    ]
