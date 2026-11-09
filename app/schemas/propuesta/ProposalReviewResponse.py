"""Schemas para la vista de revisión de propuestas."""

from pydantic import BaseModel, ConfigDict, Field


class ProposalReviewDocument(BaseModel):
    name: str
    size: str


class ProposalReviewHistory(BaseModel):
    id: str
    kind: str
    text: str
    author: str
    date: str


class ProposalReviewItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    entity: str | None
    applicant_type: str | None = Field(alias="applicantType")
    contact_name: str | None = Field(alias="contactName")
    contact_email: str | None = Field(alias="contactEmail")
    proposal_type: str | None = Field(alias="proposalType")
    description: str | None
    submitted_at: str = Field(alias="submittedAt")
    status: str
    data_complete: bool = Field(alias="dataComplete")
    has_faculty_approval: bool = Field(alias="hasFacultyApproval")
    documents: list[ProposalReviewDocument]
    history: list[ProposalReviewHistory]
