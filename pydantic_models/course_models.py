from typing import Annotated, List, TypeAlias
from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Shared helpers / custom types
# ---------------------------------------------------------------------------

HexDigest: TypeAlias = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]

# ---------------------------------------------------------------------------
# “DATA” MODELS
# ---------------------------------------------------------------------------

class ChapterData(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "chapter_title": "Introduction",
                "chapter_start_page": 1,
                "chapter_end_page": 10,
                "chapter_content": "This is the full text of the chapter...",
                "chapter_hash": "0f4a1d8e2b6a43ee91a59747b1e2c01ed8bbdcf53a5fe4d5e9c4c9b4d4d2a1b7"
            }
        }
    )

    chapter_title: str = Field(..., description="Chapter title")
    chapter_start_page: int = Field(..., ge=1, description="Start page")
    chapter_end_page: int = Field(..., ge=1, description="End page")
    chapter_content: str = Field(..., description="Full content of the chapter")
    chapter_hash: HexDigest = Field(..., description="SHA256 hash of chapter content")

    @model_validator(mode="after")
    def _check_page_order(self):
        if self.chapter_end_page < self.chapter_start_page:
            raise ValueError("chapter_end_page must be ≥ chapter_start_page")
        return self


class BookData(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "book_id": "BOOK123",
                "book_name": "Mathematics Volume 1",
                "author_name": "Utsav Vora",
                "grade_ids": ["9", "10"],
                "chapters": [ChapterData.model_config['json_schema_extra']['example']]
            }
        }
    )

    book_id: str = Field(..., description="Unique book identifier")
    book_name: str = Field(..., description="Book name")
    author_name: str = Field(..., description="Author name")
    grade_ids: List[str] = Field(..., description="Grades the book is for")
    chapters: List[ChapterData] = Field(..., description="Chapters of the book")


class CourseData(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "course_id": "CSE101",
                "course_name": "Introduction to Algorithms",
                "course_head_instructor_id": "1001",
                "course_instructor_ids": ["1002", "1003"],
                "books": [BookData.model_config['json_schema_extra']['example']]
            }
        }
    )

    course_id: str = Field(..., description="Unique course ID")
    course_name: str = Field(..., description="Course name")
    course_head_instructor_id: str = Field(..., description="Head instructor ID")
    course_instructor_ids: List[str] = Field(..., description="Other instructors")
    books: List[BookData] = Field(..., description="Recommended books for the course")


# ---------------------------------------------------------------------------
# “CONFIG / REQUEST” MODELS
# ---------------------------------------------------------------------------

class ChapterConfig(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "chapter_title": "Introduction",
                "chapter_start_page": 1,
                "chapter_end_page": 10,
            }
        }
    )

    chapter_title: str = Field(..., description="Chapter title")
    chapter_start_page: int = Field(..., ge=1, description="Start page")
    chapter_end_page: int = Field(..., ge=1, description="End page")

    @model_validator(mode="after")
    def _check_page_order(self):
        if self.chapter_end_page < self.chapter_start_page:
            raise ValueError("chapter_end_page must be ≥ chapter_start_page")
        return self


class BookConfig(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "author_name": "Utsav Vora",
                "book_name": "My Awesome Book",
                "book_drive_link": "https://drive.google.com/...",
                "grade_ids": ["10", "9"],
                "chapters": [
                    {
                        "chapter_title": "Chapter 1 - Getting Started",
                        "chapter_start_page": 1,
                        "chapter_end_page": 12,
                    },
                    {
                        "chapter_title": "Chapter 2 - Advanced Techniques",
                        "chapter_start_page": 13,
                        "chapter_end_page": 48,
                    },
                ],
            }
        }
    )

    author_name: str = Field(..., description="Author's name")
    grade_ids: List[str] = Field(..., description="Target grades")
    book_name: str = Field(..., description="Name of the book")
    book_drive_link: str = Field(..., description="Google Drive link to PDF")
    chapters: List[ChapterConfig] = Field(..., description="Chapter definitions")


class BookAddRequest(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "course_name": "Physics 101",
                "data": BookConfig.model_config["json_schema_extra"]["example"]
            }
        }
    )

    course_name: str = Field(..., description="Course name")
    data: BookConfig = Field(..., description="Book data to be added")


class CourseConfig(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "course_name": "Awesome Subject",
                "course_head_instructor_id": "1001",
                "course_instructor_ids": ["1002"],
            }
        }
    )

    course_name: str = Field(..., description="Name of the course")
    course_head_instructor_id: str = Field(..., description="Head instructor ID")
    course_instructor_ids: List[str] = Field(..., description="Other instructors")


class CourseAddRequest(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        json_schema_extra={
            "example": {
                "data": CourseConfig.model_config["json_schema_extra"]["example"]
            }
        }
    )

    data: CourseConfig = Field(..., description="Course creation payload")
