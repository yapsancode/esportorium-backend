import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_min_role
from app.models.match import Match
from app.models.tournament import Tournament, TournamentFormat, TournamentStatus
from app.models.user import User, UserRole
from app.schemas.bracket import BracketPublic, MatchPublic, RoundPublic
from app.services.bracket import generate_bracket

router = APIRouter(prefix="/tournaments/{tournament_id}", tags=["brackets"])


@router.post("/bracket/generate", response_model=list[MatchPublic], status_code=status.HTTP_201_CREATED)
def generate_tournament_bracket(
    tournament_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_min_role(UserRole.organizer))],
    session: Annotated[Session, Depends(get_session)],
) -> list[Match]:
    tournament = session.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if tournament.organizer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this tournament")
    if tournament.status != TournamentStatus.open:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tournament must be in 'open' status to generate a bracket (current: {tournament.status.value})",
        )
    if tournament.format != TournamentFormat.single_elimination:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Bracket generation is only supported for single_elimination format",
        )

    try:
        matches = generate_bracket(tournament_id, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    tournament.status = TournamentStatus.in_progress
    tournament.updated_at = datetime.now(timezone.utc)
    session.add(tournament)
    session.commit()

    return matches


@router.get("/bracket", response_model=BracketPublic)
def get_bracket(
    tournament_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
) -> BracketPublic:
    tournament = session.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")

    matches = session.exec(
        select(Match)
        .where(Match.tournament_id == tournament_id)
        .order_by(Match.round, Match.match_number)
    ).all()

    rounds: dict[int, list[MatchPublic]] = {}
    for match in matches:
        rounds.setdefault(match.round, []).append(MatchPublic.model_validate(match))

    return BracketPublic(
        tournament_id=tournament_id,
        rounds=[RoundPublic(round=r, matches=m) for r, m in sorted(rounds.items())],
    )
