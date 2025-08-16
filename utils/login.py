from fastapi import HTTPException, status
from mongo_ops import login_data
from pydantic_models.login_model import UserCreate, UserInDB


def get_password_hash(user_id: str, password: str, ph) -> str:
    combined = f"{password}{user_id}"
    return ph.hash(combined)

def check_and_add_user(user: UserCreate, ph):
    try:
        existing = login_data.get_user(user_id=user.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID already exists"
            )
        hashed_password = get_password_hash(user.user_id, user.password, ph)

        user_doc = UserInDB(
            user_id=user.user_id,
            hashed_password=hashed_password,
            user_role=user.user_role
        )
        login_data.add_user(user_doc)
    except Exception as e:
        raise e