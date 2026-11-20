from app.schemas.propuesta.ProposalComment import ProposalComments
from app.schemas.propuesta.ProposalComment import ProposalComments
from app.schemas.propuesta.ProposalReviewResponse import ProposalReviewItem


class ProposalDetailResponse(ProposalReviewItem):
    """Detalle de propuesta con la primera página de comentarios."""

    comments: ProposalComments
