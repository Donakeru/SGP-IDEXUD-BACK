"""Schemas de propuestas."""

from app.schemas.propuesta.CreateProposalDto import CreateProposalDto
from app.schemas.propuesta.ProposalListResponse import (
    ProposalListItem,
    ProposalListResponse,
)
from app.schemas.propuesta.ProposalResponse import ProposalResponse

__all__ = [
    "CreateProposalDto",
    "ProposalListItem",
    "ProposalListResponse",
    "ProposalResponse",
]
