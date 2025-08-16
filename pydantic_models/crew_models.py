from typing import List, Literal
from pydantic import BaseModel

from pydantic_models.announcement_model import AnnouncementData
from pydantic_models.exam_models import QuestionAnswerData
from pydantic_models.login_model import Metadata
from pydantic_models.student_exam_performance_models import QuestionAnswerFeedbackDataForInstructor
from pydantic_models.support_ticket_models import ReturnSupportTicketDataRequestAssignee


# performance crew models 

class IdentifyParametersResponse(BaseModel):
    found_parameters: List[str]
    missing_parameters: List[str]
    suggested_tool_call: List[str]
    found_parameters_with_values: List[object]

class ResponseModel(BaseModel):
    response: str
    found_parameters: List[str]
    suggested_tool_call: List[str]
    has_all_fields: bool

class FinalResponseModel(BaseModel):
    response: str

class RaiseTicketModel(BaseModel):
    response: str
    support_ticket_id: str

class ApproveSuggestionModel(BaseModel):
    response: str
    support_ticket_id: str
    resolved: bool

class FixSuggestionModel(BaseModel):
    suggested_reply: str
    response: str

class GatherPerformanceReport(BaseModel):
    parameters: object
    information: str
    done_tool_call: bool

# subjective crew models

class ContentFromHistory(BaseModel):
    content_from_history: str

class SubjectiveCrewAnswer(BaseModel):
    context: str
    source: List[str]
    content_from_history: str
    response: str
    last_subject: List[str]

class RetrievedContent(BaseModel):
    context: str
    source: List[str]

class RetrievedContentWithoutSource(BaseModel):
    context: str

class ClassifiedSubject(BaseModel):
    subjects: List[str]

# supervisor crew models

class RoutingOutput(BaseModel):
    route: Literal["course", "support", "performance", "out_of_scope"]
    reason: Literal["follow_up", "new_query"]
    response: str

# fetch ticket crew models

class IdentifySupportTicketIdResponse(BaseModel):
    user_input: str
    has_ticket_id: bool

# support intent crew model

class SupportIntentOutput(BaseModel):
    intent: Literal["administrative_query", "escalation", "ticket_creation", "ticket_details"]

# raise ticket crew models

class FollowUpForMoreInfo(BaseModel):
    response: str
    follow_up_needed: bool

# teachers

class RoutingOutputTeacher(BaseModel):
    route: Literal["ticket_activity", "evaluation_activity", "announcement_activity", "answer_key_generation_activity", "out_of_scope"]
    reason: Literal["follow_up", "new_query"]
    response: str

class TicketHandlerIntentOutput(BaseModel):
    sub_route: Literal["support_ticket_detail", "resolve_ticket", "approve_suggestion", "fix_suggestion"]

class AnnouncementIntentOutput(BaseModel):
    sub_route: Literal["announcement_detail", "announcement_creator", "announcement_approved", "announcement_fix"]

class EvaluatorIntentOutput(BaseModel):
    sub_route: Literal["evaluation_details", "evaluation_feedback", "approve_feedback", "fix_feedback"]

class AnswerKeyIntentOutput(BaseModel):
    sub_route: Literal["answer_key_details", "approve_answer_key", "fix_answer_key"]

class IdentifySupportIdResponse(BaseModel):
    support_ticket_id: str
    support_ticket_found: bool
    metadata: Metadata

class SupportTicketData(BaseModel):
    support_ticket_id: str
    support_ticket_data: ReturnSupportTicketDataRequestAssignee

class SupportTicketDataFetcherResponse(BaseModel):
    response: str
    support_ticket_id: str

class SuggestedToolCall(BaseModel):
    support_ticket_id: str
    tool_response: ReturnSupportTicketDataRequestAssignee

class SuggestedToolCallResponse(BaseModel):
    support_ticket_id: str
    suggested_reply: str
    response: str

class SupportTicketID(BaseModel):
    support_ticket_id: str

class AnnouncementCrewData(BaseModel):
    announcement_id: str
    announcement_data: AnnouncementData

class AnnouncementCrewResponseData(BaseModel):
    announcement_id: str
    response: str

class AnnouncementFindParametersResponse(BaseModel):
    announcement_class: str
    announcement_summary: str
    announcement_event_date: str
    response: str

class AnnouncementDraftResponse(BaseModel):
    announcement_class: str
    announcement_summary: str
    announcement_event_date: str
    announcement_title: str
    draft_announcement: str

class CreateAnnouncementResponse(BaseModel):
    response: str
    announcement_id: str
    resolved: bool

class EvaluationDetailParams(BaseModel):
    evaluation_exam: str
    evaluation_class: str
    evaluation_subject: str
    response: str

class EvaluationToolResponse(BaseModel):
    evaluation_details: str

class EvaluationData(BaseModel):
    evaluation_exam: str
    evaluation_class: str
    evaluation_subject: str
    response: str

class StudentID(BaseModel):
    student_id: str

class EvaluationFeedbackData(BaseModel):
    suggested_evaluation_feedback: List[QuestionAnswerFeedbackDataForInstructor]

class EvaluationFeedbackResponse(BaseModel):
    student_id: str
    suggested_evaluation_feedback_list: List[QuestionAnswerFeedbackDataForInstructor]
    suggested_evaluation_feedback_section: str

class EvaluationFeedbackResponse2(BaseModel):
    student_id: str
    suggested_evaluation_feedback_list: List[QuestionAnswerFeedbackDataForInstructor]

class EvaluationSubmitModel(BaseModel):
    response: str
    resolved: bool

class FixEvaluationFeedback(BaseModel):
    suggested_evaluation_feedback: str
    evaluation_feedback_list: List[QuestionAnswerFeedbackDataForInstructor]

class FixEvaluationFeedback2(BaseModel):
    individual_mark: int
    similarity_score: int
    feedback: str

class AnswerKeyDetailParams(BaseModel):
    answer_key_exam: str
    answer_key_class: str
    answer_key_subject: str
    response: str

class AnswerKeyDetailMidResponse(BaseModel):
    answer_key_exam: str
    answer_key_class: str
    answer_key_subject: str
    generated_answer_key: str

class AnswerKeyDetailResponse(BaseModel):
    answer_key_exam: str
    answer_key_class: str
    answer_key_subject: str
    generated_answer_key_list: List[QuestionAnswerData]

class AnswerKeyToolResponse(BaseModel):
    answer_key_detail: List[QuestionAnswerData]

class AnswerKeySubmitModel(BaseModel):
    response: str
    resolved: bool

class FetchQuestionNumber(BaseModel):
    question_number: int

class AnswerKeyFixModel(BaseModel):
    generated_answer_key: str
    generated_answer_key_list: List[QuestionAnswerData]
    response: str

class AnswerKeyFixModel2(BaseModel):
    updated_answer: str

class EvaluateStudentResponse(BaseModel):
    marks: int
    feedback: str

class AdministrativeQueryRewritter(BaseModel):
    query_list: List[str]

class AdministrativeModelOutput(BaseModel):
    answer_list_response: List[str]