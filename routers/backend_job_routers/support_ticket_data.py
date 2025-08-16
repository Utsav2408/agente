from fastapi import APIRouter, HTTPException
from pydantic_models.support_ticket_models import SupportTicketSpec
from utils import support_ticket

router = APIRouter(
    tags=["Support Ticket"]
)

@router.post("/support")
def add_support_ticket_data(request: SupportTicketSpec):
    try:
        support_ticket.add_support_ticket(request)
        return {"message": "Successfully added the ticket data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))