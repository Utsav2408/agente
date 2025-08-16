from pymongo.collection import Collection

from config.mongo_connect import mongo
from constant.constant import LOGIN_DB, LOGIN_DB_COLLECTION
from mongo_ops.utils import _to_doc
from pydantic_models.login_model import UserInDB


# ---------------------------------------------------------------------------
# Mongo connection (opened once, reused)
# ---------------------------------------------------------------------------
_login_col: Collection = mongo.get_connection()[LOGIN_DB][LOGIN_DB_COLLECTION]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def add_user(user: UserInDB):
    result = _login_col.insert_one(_to_doc(user))
    return result.inserted_id


def get_user_role(user_id: str) -> str:
    doc = _login_col.find_one(
        {"user_id": user_id},
        {"_id": 0},
    )
    return doc['user_role']

def get_user(user_id: str) -> UserInDB:
    doc = _login_col.find_one(
        {"user_id": user_id},
        {"_id": 0},
    )
    return UserInDB.model_validate(doc) if doc else None