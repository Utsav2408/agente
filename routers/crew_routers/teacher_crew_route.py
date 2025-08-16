import jwt
import os
from fastapi import APIRouter, HTTPException, Header, status
from jwt import ExpiredSignatureError, PyJWTError

from constant.constant import ALGORITHM
from crew_flows_teacher.main import kickoff
from pydantic_models.query_model import InstructorQueryRequest

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")

router = APIRouter(
    tags=["Teacher Crew"]
)

@router.post(
    "/teacher/query",
    responses={403: {"description": "Forbidden - invalid or expired token"}}
)
async def interact_teacher_crew(
    request: InstructorQueryRequest,
    authorization: str = Header(..., description="Authorization header: Bearer <token>")
):
    # 1) Extract Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated"
        )
    token = authorization.split(" ", 1)[1]

    # 2) Validate JWT
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token expired"
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token"
        )

    # 3) Delegate to the flow with session_token
    try:
        return await kickoff(
            instructor_id=request.instructor_id,
            instructor_email=request.instructor_email,
            user_query=request.query,
            session_token=token,
            available_subjects=request.available_subjects
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
