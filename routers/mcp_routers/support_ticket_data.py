from typing import List
from fastapi import APIRouter, HTTPException
from pydantic_models.query_model import AnswerList, QueryList
from pydantic_models.support_ticket_models import ResolveTicketSpec, ReturnSupportTicketDataRequestAssignee, ReturnSupportTicketForAssignee, SupportTicketID, SupportTicketSpec, ReturnSupportTicketData, ReturnSupportTicketSuggestion
import httpx, os
from dotenv import load_dotenv
from utils import support_ticket
from mongo_ops.support_ticket_data import (
    get_all_support_ticket_for_assignee,
    get_support_ticket_by_id,
    get_all_support_ticket_by_student_id,
    get_support_ticket_by_id_for_assignee,
    update_assignee_reply,
)

load_dotenv()

router = APIRouter(
    tags=["Support Ticket"]
)

# students

@router.post(
    path="/user/support",
    operation_id="raise_support_ticket_tool",
    description="Use this function to capture user's support request and store in db"
)
def raise_support_ticket_tool(request: SupportTicketSpec) -> SupportTicketID:
    """
    Use this function to capture user's support request and store in db.

    Args:
        request (SupportTicketSpec): The request body containing user's support ticket details.

    Returns:
        SupportTicketID containing the unique identifier of support ticket raised

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        support_ticket_id = support_ticket.add_support_ticket(request)
        return SupportTicketID(
            support_ticket_id=support_ticket_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    path="/support/{support_ticket_id}",
    operation_id="get_support_ticket_by_id",
    description="Retrieve a support ticket by its unique ID",
    response_model=ReturnSupportTicketData,
)
def get_support_ticket(support_ticket_id: str) -> ReturnSupportTicketData:
    """
    Retrieve a single support ticket by its unique ticket ID.

    Args:
        support_ticket_id (str): Unique identifier of the support ticket.

    Returns:
        ReturnSupportTicketData: The ticket details for the given ID.

    Raises:
        HTTPException 404: If no ticket is found with the provided ID.
        HTTPException 500: For any unexpected internal errors.
    """
    try:
        ticket = get_support_ticket_by_id(support_ticket_id)
        return ticket
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    path="/support/student/{student_id}",
    operation_id="get_all_support_ticket_by_student_id",
    description="Retrieve all support tickets submitted by a student",
    response_model=List[ReturnSupportTicketData],
)
def list_support_tickets_by_student(student_id: str) -> List[ReturnSupportTicketData]:
    """
    Retrieve all support tickets for a specific student.

    Args:
        student_id (str): The ID of the student whose tickets are to be fetched.

    Returns:
        List[ReturnSupportTicketData]: A list of ticket details for the student.

    Raises:
        HTTPException 500: For any unexpected internal errors.
    """
    try:
        tickets = get_all_support_ticket_by_student_id(student_id)
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    path="/user/query/administrative",
    operation_id="fetch_answer_administrative_tool",
    description="Use this function to capture user query related to canvas or administration and return back the answer"
)
async def fetch_answer_administrative_tool(request: QueryList) -> AnswerList:
    """
    Use this function to capture user query related to canvas or administration and return back the answer.

    Args:
        request (QueryList): The request body containing a list of queries derived from user's query.

    Returns:
        A list of answers generated for each query in the list entered.

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        api_key = os.getenv("LANGFLOW_API_KEY")
        url = os.getenv("LANGFLOW_URL")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }

        answer_list = []
        timeout = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)

        async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
            for query in request.query_list[:2]:
                payload = {
                    "output_type": "chat",
                    "input_type": "chat",
                    "input_value": query
                }
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                answer_list.append(
                    data["outputs"][0]["outputs"][0]["outputs"]["message"]["message"]
                )

        return AnswerList(answer_list=answer_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# teachers

@router.get(
    path="/support/assignee/{assignee}",
    operation_id="get_all_support_ticket_by_assignee",
    description="Retrieve all support tickets assigned to an assignee",
    response_model=ReturnSupportTicketDataRequestAssignee,
)
def list_support_tickets_for_assignee(assignee: str) -> ReturnSupportTicketDataRequestAssignee:
    """
    Retrieve all support tickets assigned to an assignee.

    Args:
        assignee (str): The email ID of the assignee whose assigned tickets are to be fetched.

    Returns:
        ReturnSupportTicketDataRequestAssignee: A list of ticket details for the assignee to review and its count

    Raises:
        HTTPException 500: For any unexpected internal errors.
    """
    try:
        tickets = get_all_support_ticket_for_assignee(assignee)
        return ReturnSupportTicketDataRequestAssignee(
            data=tickets,
            count=len(tickets)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    path="/support/{support_ticket_id}/assignee",
    operation_id="get_support_ticket_by_id_request_assignee",
    description="Retrieve a support ticket by its unique ID when requested by assignee",
    response_model=ReturnSupportTicketDataRequestAssignee,
)
def get_support_ticket_request_assignee(support_ticket_id: str) -> ReturnSupportTicketDataRequestAssignee:
    """
    Retrieve a single support ticket by its unique ticket ID when asked by assignee

    Args:
        support_ticket_id (str): Unique identifier of the support ticket.

    Returns:
        ReturnSupportTicketDataRequestAssignee: The ticket details for the given ID requested by assignee and count as 1

    Raises:
        HTTPException 404: If no ticket is found with the provided ID.
        HTTPException 500: For any unexpected internal errors.
    """
    try:
        ticket = get_support_ticket_by_id(support_ticket_id)
        if ticket.resolved:
            return ReturnSupportTicketDataRequestAssignee(
                data=[],
                count=0
            )
        else:
            return ReturnSupportTicketDataRequestAssignee(
                data=[ReturnSupportTicketForAssignee(**ticket.model_dump())],
                count=1
            )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get(
    path="/support/{support_ticket_id}/suggestion/assignee",
    operation_id="get_support_ticket_suggestion_request_assignee",
    description="Retrieve the suggested reply for a support ticket using its unique ID when requested by assignee",
    response_model=ReturnSupportTicketDataRequestAssignee,
)
def get_support_ticket_suggestion_request_assignee(support_ticket_id: str) -> ReturnSupportTicketDataRequestAssignee:
    """
    Retrieve the suggested reply for a support ticket using its unique ticket ID when asked by assignee

    Args:
        support_ticket_id (str): Unique identifier of the support ticket.

    Returns:
        ReturnSupportTicketDataRequestAssignee: The ticket details along with suggested reply for the given ID requested by assignee and count as 1

    Raises:
        HTTPException 404: If no ticket is found with the provided ID.
        HTTPException 500: For any unexpected internal errors.
    """
    try:
        ticket = get_support_ticket_by_id_for_assignee(support_ticket_id)

        return ReturnSupportTicketDataRequestAssignee(
            data=[ReturnSupportTicketSuggestion(
                support_ticket_id=ticket.support_ticket_id,
                support_content=ticket.support_content,
                created_at=ticket.created_at,
                suggested_reply=ticket.suggested_reply
            )],
            count=1
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post(
    path="/assignee/support/resolve",
    operation_id="resolve_support_ticket_tool",
    description="Use this function to capture user's support request and store in db"
)
def resolve_support_ticket_tool(request: ResolveTicketSpec) -> str:
    """
    Use this function to resolve support ticket using the reply assignee agreed on.

    Args:
        request (ResolveTicketSpec): The request body containing support ticket ID to resolve and the reply to which assignee agreed on.

    Returns:
        success msg if ticket was resolved else failure msg if ticket was not resolved.

    Raises:
        HTTPException: If an internal error occurs.
    """
    try:
        update_assignee_reply(request.support_ticket_id, request.assignee_reply)
        return "Successfully resolved ticket."
    except Exception as e:
        return "Failed to resolve the ticket."