import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import require_min_role
from app.models.match import Match, MatchStatus
from app.models.tournament import Tournament
from app.models.user import User, UserRole
from app.schemas.bracket import MatchPublic, ScoreReport
from app.services.bracket import advance_winner

router = APIRouter(prefix="/matches", tags=["matches"])


@router.patch("/{match_id}/score", response_model=MatchPublic)
def report_score(
    match_id: uuid.UUID,
    data: ScoreReport,
    current_user: Annotated[User, Depends(require_min_role(UserRole.organizer))],
    session: Annotated[Session, Depends(get_session)],
) -> Match:
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    tournament = session.get(Tournament, match.tournament_id)
    if tournament.organizer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this tournament")

    if match.status == MatchStatus.bye:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot report score for a bye match")
    if match.status == MatchStatus.completed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match is already completed")

    valid_participants = {p for p in (match.participant_1, match.participant_2) if p is not None}
    if data.winner_id not in valid_participants:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="winner_id must be one of the match participants",
        )

    match.score_1 = data.score_1
    match.score_2 = data.score_2
    match.winner_id = data.winner_id
    match.status = MatchStatus.completed
    match.updated_at = datetime.now(timezone.utc)
    session.add(match)
    session.commit()
    session.refresh(match)

    advance_winner(match, session)

    return match
