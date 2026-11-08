"""Schema de entrada para el registro de propuestas."""

from datetime import date
from typing import Self

from fastapi import File, Form, UploadFile
from pydantic import BaseModel, ConfigDict, Field


class CreateProposalDto(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="forbid",
    )

    applicant_type: str = Field(alias="applicantType")
    organization_name: str = Field(alias="organizationName")
    nit: str
    contact_name: str = Field(alias="contactName")
    contact_role: str = Field(alias="role")
    email: str
    phone: str
    title: str
    proposal_type: str = Field(alias="proposalType")
    description: str
    justification: str
    start_date: date = Field(alias="startDate")
    privacy_accepted: bool = Field(alias="privacyAccepted")
    proposal_files: list[UploadFile] = Field(
        default_factory=list,
        alias="proposalFiles",
    )
    faculty_files: list[UploadFile] = Field(
        default_factory=list,
        alias="facultyFiles",
    )

    @classmethod
    def as_form(
        cls,
        applicant_type: str = Form(..., alias="applicantType"),
        organization_name: str = Form(..., alias="organizationName"),
        nit: str = Form(...),
        contact_name: str = Form(..., alias="contactName"),
        contact_role: str = Form(..., alias="role"),
        email: str = Form(...),
        phone: str = Form(...),
        title: str = Form(...),
        proposal_type: str = Form(..., alias="proposalType"),
        description: str = Form(...),
        justification: str = Form(...),
        start_date: date = Form(..., alias="startDate"),
        privacy_accepted: bool = Form(..., alias="privacyAccepted"),
        proposal_files: list[UploadFile] | None = File(
            default=None,
            alias="proposalFiles",
        ),
        faculty_files: list[UploadFile] | None = File(
            default=None,
            alias="facultyFiles",
        ),
    ) -> Self:
        return cls(
            applicantType=applicant_type,
            organizationName=organization_name,
            nit=nit,
            contactName=contact_name,
            role=contact_role,
            email=email,
            phone=phone,
            title=title,
            proposalType=proposal_type,
            description=description,
            justification=justification,
            startDate=start_date,
            privacyAccepted=privacy_accepted,
            proposalFiles=proposal_files or [],
            facultyFiles=faculty_files or [],
        )
