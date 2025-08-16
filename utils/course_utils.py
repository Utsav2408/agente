from pydantic_models.course_models import BookConfig, CourseConfig, CourseData
from mongo_ops import course_data
from document_processing import utils


def add_course(course_config: CourseConfig):
    try:
        course = CourseData(
            course_id=course_config.course_name.lower().replace(" ", "_"),
            course_name=course_config.course_name,
            course_head_instructor_id=course_config.course_head_instructor_id,
            course_instructor_ids=course_config.course_instructor_ids,
            books=[]
        )
        course_data.insert_course(course)
    except Exception as e:
        raise e
    

def add_book(course_name: str, book_config: BookConfig):
    try:
        course = course_data.get_course_by_name(course_name)
        utils.process_books(course.course_id, book_config)
    except Exception as e:
        raise e