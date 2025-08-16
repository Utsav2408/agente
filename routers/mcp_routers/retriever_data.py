from fastapi import APIRouter, HTTPException
from faiss_ops.faiss_db import retrieve_relevant_context, retrieve_relevant_doc_subjective
from pydantic_models.retrieval_model import RetrievedContext, RetrievedSubjectiveContext, SubjectiveQuery


router = APIRouter(
    tags=["Course"]
)


@router.post(
    path="/retrieve/subjective",
    operation_id="retrieve_for_subjective_agent",
    description="Use this function to get the relevant context along with source from the vector db for a particular query.",
    response_model=RetrievedSubjectiveContext
)
def retrieve_for_subjective_agent(request: SubjectiveQuery) -> RetrievedSubjectiveContext:
    """
    Use this function to get the relevant context along with source from the vector db for a particular query.

    Args:
        request (SubjectiveQuery): The request body containing user's query.

    Returns:
        JSON: containing a combined string of context and combined string of source for each context.

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        context, source = retrieve_relevant_doc_subjective(
            course_name=request.subject_names,
            grade=request.grade,
            query=request.query
        )

        return RetrievedSubjectiveContext(
            context=context,
            source=source
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post(
    path="/retrieve/context",
    operation_id="retrieve_context",
    description="Use this function to get the relevant context from the vector db for a particular query.",
    response_model=RetrievedContext
)
def retrieve_context(request: SubjectiveQuery) -> RetrievedContext:
    """
    Use this function to get the relevant context from the vector db for a particular query.

    Args:
        request (SubjectiveQuery): The request body containing user's query.

    Returns:
        JSON: containing a combined string of context retrieved.

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        context = retrieve_relevant_context(
            course_name=request.subject_names,
            grade=request.grade,
            query=request.query
        )

        return RetrievedContext(
            context=context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))