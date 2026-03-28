import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_min_role
from app.models.dispute import Dispute, DisputeStatus
from app.models.match import Match, MatchStatus
from app.models.user import User, UserRole
from app.schemas.dispute import DisputeCreate, DisputePublic, DisputeResolve

router = APIRouter(tags=["disputes"])


@router.post("/matches/{match_id}/dispute", response_model=DisputePublic, status_code=status.HTTP_201_CREATED)
def raise_dispute(
    match_id: uuid.UUID,
    data: DisputeCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Dispute:
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    if match.status != MatchStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Disputes can only be raised on completed matches",
        )

    if current_user.id not in (match.participant_1, match.participant_2):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only match participants can raise a dispute",
        )

    active_dispute = session.exec(
        select(Dispute).where(
            Dispute.match_id == match_id,
            Dispute.status != DisputeStatus.resolved,
        )
    ).first()
    if active_dispute:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An open or under-review dispute already exists for this match",
        )

    dispute = Dispute(match_id=match_id, raised_by=current_user.id, **data.model_dump())
    session.add(dispute)
    session.commit()
    session.refresh(dispute)
    return dispute


@router.get("/disputes", response_model=list[DisputePublic])
def list_open_disputes(
    current_user: Annotated[User, Depends(require_min_role(UserRole.moderator))],
    session: Annotated[Session, Depends(get_session)],
) -> list[Dispute]:
    return session.exec(
        select(Dispute).where(Dispute.status != DisputeStatus.resolved)
    ).all()


@router.patch("/disputes/{dispute_id}/resolve", response_model=DisputePublic)
def resolve_dispute(
    dispute_id: uuid.UUID,
    data: DisputeResolve,
    current_user: Annotated[User, Depends(require_min_role(UserRole.moderator))],
    session: Annotated[Session, Depends(get_session)],
) -> Dispute:
    dispute = session.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    if dispute.status == DisputeStatus.resolved:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dispute is already resolved")

    match = session.get(Match, dispute.match_id)
    if match:
        match.status = MatchStatus.pending
        match.winner_id = None
        match.score_1 = 0
        match.score_2 = 0
        match.updated_at = datetime.now(timezone.utc)
        session.add(match)

    dispute.status = DisputeStatus.resolved
    dispute.resolved_by = current_user.id
    dispute.resolution = data.resolution
    dispute.updated_at = datetime.now(timezone.utc)
    session.add(dispute)
    session.commit()
    session.refresh(dispute)
    return dispute
