from typing import Optional
from bson import ObjectId
from pymongo.collection import Collection

from config.mongo_connect import mongo
from constant.constant import GRADE_DB_COLLECTION, ACADEMIC_DB_NAME
from mongo_ops.utils import _to_doc
from pydantic_models.grade_models import GradeData


# ---------------------------------------------------------------------------
# Mongo connection (opened once, reused)
# ---------------------------------------------------------------------------
_grade_col: Collection = mongo.get_connection()[ACADEMIC_DB_NAME][GRADE_DB_COLLECTION]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def add_grade(grade_data: GradeData) -> ObjectId:
    """
    Insert a new grade record.

    Returns
    -------
    bson.ObjectId
        The MongoDB `_id` of the inserted document.
    """
    result = _grade_col.insert_one(_to_doc(grade_data))
    return result.inserted_id


def get_grade_data(grade: str) -> Optional[GradeData]:
    """
    Retrieve a grade document by its `grade` identifier.

    Returns
    -------
    GradeData | None
        Parsed grade data, or `None` if the grade does not exist.
    """
    doc = _grade_col.find_one(
        {"grade": grade},
        {"_id": 0},  # hide internal Mongo ID
    )
    return GradeData.model_validate(doc) if doc else None
