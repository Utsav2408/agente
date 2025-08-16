from typing import Optional
from bson import ObjectId
from pymongo.collection import Collection

from config.mongo_connect import mongo
from constant.constant import STUDENT_DB_COLLECTION, STUDENT_DB_NAME
from mongo_ops.utils import _to_doc
from mongo_ops import course_data
from pydantic_models.student_models import StudentData, StudentDataWithoutNumber

# ---------------------------------------------------------------------------
# Mongo connection (opened once, reused for every call)
# ---------------------------------------------------------------------------

_student_col: Collection = mongo.get_connection()[STUDENT_DB_NAME][STUDENT_DB_COLLECTION]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def add_student(student_data: StudentData) -> ObjectId:
    """
    Insert a new student record.

    Returns
    -------
    bson.ObjectId
        The MongoDB `_id` of the newly inserted document.
    """
    result = _student_col.insert_one(_to_doc(student_data))
    return result.inserted_id


def get_student_public(student_id: str) -> Optional[StudentDataWithoutNumber]:
    """
    Retrieve a student without exposing phone numbers.

    Returns
    -------
    StudentDataWithoutNumber | None
        The public view of the student, or `None` if not found.
    """
    doc = _student_col.find_one(
        {"student_id": student_id},
        {  # projection: fetch only the needed fields
            "_id": 0,
            "student_id": 1,
            "first_name": 1,
            "last_name": 1,
            "grade": 1,
            "course_ids": 1,
        },
    )
    course_names = []
    for course_id in doc['course_ids']:
        course_names.append(course_data.get_course_by_id(course_id).course_name)
    

    return StudentDataWithoutNumber(
        student_id=doc['student_id'],
        first_name=doc['first_name'],
        last_name=doc['last_name'],
        grade=doc['grade'],
        course_names=course_names
    )
