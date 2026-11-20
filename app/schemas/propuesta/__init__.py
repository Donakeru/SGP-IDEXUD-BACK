"""Schemas de propuestas."""

from app.schemas.propuesta.CreateProposalDto import CreateProposalDto
from app.schemas.propuesta.ProposalComment import ProposalComment, ProposalComments
from app.schemas.propuesta.ProposalCommentRequest import ProposalCommentRequest
from app.schemas.propuesta.ProposalDetailResponse import ProposalDetailResponse
from app.schemas.propuesta.ProposalDocumentUploadResponse import (
    ProposalDocumentUploadResponse,
)
from app.schemas.propuesta.ProposalListResponse import (
    ProposalListItem,
    ProposalListResponse,
)
from app.schemas.propuesta.ProposalResponse import ProposalResponse
from app.schemas.propuesta.ProposalReviewResponse import (
    ProposalReviewDocument,
    ProposalReviewHistory,
    ProposalReviewItem,
)
from app.schemas.propuesta.ProposalStateChange import (
    ProposalStateChangeRequest,
    ProposalStateChangeResponse,
)

__all__ = [
    "CreateProposalDto",
    "ProposalComment",
    "ProposalComments",
    "ProposalCommentRequest",
    "ProposalDetailResponse",
    "ProposalDocumentUploadResponse",
    "ProposalListItem",
    "ProposalListResponse",
    "ProposalResponse",
    "ProposalReviewDocument",
    "ProposalReviewHistory",
    "ProposalReviewItem",
    "ProposalStateChangeRequest",
    "ProposalStateChangeResponse",
]
