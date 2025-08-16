from bson import ObjectId
from pymongo.collection import Collection
from typing import List

from config.mongo_connect import mongo
from constant.constant import SUPPORT_TICKET_COLLECTION, SUPPORT_TICKET_DB
from mongo_ops.utils import _to_doc
from pydantic_models.support_ticket_models import ReturnSupportTicketDataForAssignee, SupportTicketData, ReturnSupportTicketData, ReturnAllSupportTicketForAssignee


# ---------------------------------------------------------------------------
# Mongo connection (opened once, reused)
# ---------------------------------------------------------------------------
_support_ticket_col: Collection = mongo.get_connection()[SUPPORT_TICKET_DB][SUPPORT_TICKET_COLLECTION]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def add_support_ticket(support_ticket: SupportTicketData) -> ObjectId:
    """
    Insert a new support ticket.

    Returns
    -------
    bson.ObjectId
        The MongoDB `_id` of the inserted document.
    """
    result = _support_ticket_col.insert_one(_to_doc(support_ticket))
    return result.inserted_id


def get_support_ticket_by_id(support_ticket_id: str) -> ReturnSupportTicketData:
    """
    Retrieve a single support ticket by its unique identifier.

    Parameters
    ----------
    support_ticket_id : str
        The unique ticket ID to look up.

    Returns
    -------
    ReturnSupportTicketData
        The support ticket data.

    Raises
    ------
    ValueError
        If no ticket with the given ID is found.
    """
    doc = _support_ticket_col.find_one({"support_ticket_id": support_ticket_id})
    if not doc:
        raise ValueError(f"Support ticket with id '{support_ticket_id}' not found.")
    # Remove MongoDB internal fields if present
    doc.pop("_id", None)
    return ReturnSupportTicketData(**doc)


def get_support_ticket_by_id_for_assignee(support_ticket_id: str) -> ReturnSupportTicketDataForAssignee:
    """
    Retrieve a single support ticket by its unique identifier for assignee

    Parameters
    ----------
    support_ticket_id : str
        The unique ticket ID to look up.

    Returns
    -------
    ReturnSupportTicketDataForAssignee
        The support ticket data.

    Raises
    ------
    ValueError
        If no ticket with the given ID is found.
    """
    doc = _support_ticket_col.find_one({"support_ticket_id": support_ticket_id})
    if not doc:
        raise ValueError(f"Support ticket with id '{support_ticket_id}' not found.")
    # Remove MongoDB internal fields if present
    doc.pop("_id", None)
    return ReturnSupportTicketDataForAssignee(**doc)


def get_all_support_ticket_by_student_id(student_id: str) -> List[ReturnSupportTicketData]:
    """
    Retrieve all support tickets submitted by a given student.

    Parameters
    ----------
    student_id : str
        The student ID to filter tickets by.

    Returns
    -------
    List[ReturnSupportTicketData]
        A list of support tickets for the student.
    """
    cursor = _support_ticket_col.find({"student_id": student_id})
    tickets: List[ReturnSupportTicketData] = []
    for doc in cursor:
        doc.pop("_id", None)
        tickets.append(ReturnSupportTicketData(**doc))
    return tickets


def get_all_support_ticket_for_assignee(assignee: str) -> List[ReturnAllSupportTicketForAssignee]:
    """
    Retrieve all support tickets assigned to an assignee.

    Parameters
    ----------
    assignee : str
        The assignee to filter tickets by.

    Returns
    -------
    List[ReturnSupportTicketDataForAssignee]
        A list of support tickets assigned to the assignee.
    """
    cursor = _support_ticket_col.find({"assignee": assignee, "resolved": False})
    tickets: List[ReturnAllSupportTicketForAssignee] = []
    for doc in cursor:
        doc.pop("_id", None)
        tickets.append(ReturnAllSupportTicketForAssignee(**doc))
    return tickets

def update_suggested_reply(support_ticket_id: str, suggested_reply: str) -> int:
    """
    Update support ticket with suggested reply.

    Returns
    -------
    None
    """
    result = _support_ticket_col.update_one(
        {"support_ticket_id": support_ticket_id},
        {"$set": {"suggested_reply": suggested_reply, "checked": True}}
    )
    return result.modified_count

def update_assignee_reply(support_ticket_id: str, assignee_reply: str) -> int:
    """
    Update support ticket with assignee reply.

    Returns
    -------
    None
    """
    result = _support_ticket_col.update_one(
        {"support_ticket_id": support_ticket_id},
        {"$set": {"assignee_reply": assignee_reply, "resolved": True}}
    )
    return result.modified_count