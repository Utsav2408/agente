import jwt
import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Header, status
from jwt import ExpiredSignatureError, PyJWTError
from constant.constant import ALGORITHM
from mongo_ops import login_data
from utils import login
from redis_db.redis_client import redis_client
from pydantic_models.login_model import (
    TokenValidationResponse,
    UserCreate,
    UserLogin,
    UserVerifyResponse,
    CustomMemory,
    CustomMemoryTeacher
)
from argon2 import PasswordHasher
from dotenv import load_dotenv

load_dotenv()

# Secret & settings for JWT
SECRET_KEY = os.getenv("SECRET_KEY")
TTL_HOURS = 2

ph = PasswordHasher(memory_cost=int(os.getenv("PH_CONFIG_MEMORY_1")) * int(os.getenv("PH_CONFIG_MEMORY_2")), time_cost=int(os.getenv("PH_CONFIG_TIME")), parallelism=int(os.getenv("PH_CONFIG_PARALLELISM")))

router = APIRouter(tags=["Login"])

@router.get(
    "/validate-token",
    response_model=TokenValidationResponse,
    responses={
        401: {"description": "Missing or invalid token"},
        422: {"description": "Malformed Authorization header"},
    },
)
async def validate_token(authorization: str = Header(..., description="Bearer <JWT token>")):
    # 1) check header format
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Authorization header must be: Bearer <token>",
        )

    # 2) decode & validate
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # 3) extract claims
    user_id = payload.get("sub")
    user_role = payload.get("role")
    exp_ts = payload.get("exp")
    expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else None

    return TokenValidationResponse(
        valid=True,
        user_id=user_id,
        user_role=user_role,
        expires_at=expires_at,
    )

@router.post(
    "/verify",
    response_model=UserVerifyResponse,
    responses={401: {"description": "Invalid credentials"}, 404: {"description": "User not found"}},
)
async def verify_user(user_login: UserLogin):
    try:
        # 1) lookup & verify credentials
        user_doc = login_data.get_user(user_id=user_login.user_id)
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        combined = f"{user_login.password}{user_login.user_id}"
        if not ph.verify(user_doc.hashed_password, combined):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # 2) create JWT session token
        expire = datetime.now(timezone.utc) + timedelta(hours=TTL_HOURS)
        payload = {"sub": user_doc.user_id, "role": user_doc.user_role, "exp": expire.timestamp()}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        # 3) initialize empty memory in Redis under that token
        initial_memory = ""
        if user_doc.user_role == "student":
            initial_memory = CustomMemory().model_dump_json()
        else:
            initial_memory = CustomMemoryTeacher().model_dump_json()

        await redis_client.insert(
            f"session:{token}",
            initial_memory,
            int(timedelta(hours=TTL_HOURS).total_seconds()),
        )

        return UserVerifyResponse(
            user_id=user_doc.user_id,
            user_role=user_doc.user_role,
            verified=True,
            session_token=token,
        )

    except HTTPException as e:
        print(e)
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/role")
def get_user_role(user_id: str):
    try:
        return login_data.get_user_role(user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register")
def add_user(request: UserCreate):
    try:
        login.check_and_add_user(user=request, ph=ph)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/memory")
async def get_session_memory(
    authorization: str = Header(..., description="Bearer <JWT token>"),
):
    # 1) check header format
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Authorization header must be: Bearer <token>",
        )

    # 2) decode & validate JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # 3) fetch memory from Redis
    raw = await redis_client.get(f"session:{token}")
    if raw:
        if payload.get("role") == "student":
            try:
                memory = CustomMemory.model_validate_json(raw)
            except Exception as e:
                memory = CustomMemory()
        else:
            try:
                memory = CustomMemoryTeacher.model_validate_json(raw)
            except Exception as e:
                memory = CustomMemoryTeacher()
    else:
        if payload.get("role") == "student":
            memory = CustomMemory()
        else:
            memory = CustomMemoryTeacher()

    return memory
