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
from app.schemas.bracket import BracketPublic, MatchPublic, ParticipantUser, RoundPublic
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

    existing = session.exec(select(Match).where(Match.tournament_id == tournament_id)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bracket already generated")

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

    # Collect all participant UUIDs to resolve in one query
    participant_ids: set[uuid.UUID] = set()
    for match in matches:
        if match.participant_1:
            participant_ids.add(match.participant_1)
        if match.participant_2:
            participant_ids.add(match.participant_2)
        if match.winner_id:
            participant_ids.add(match.winner_id)

    users: dict[uuid.UUID, User] = {}
    if participant_ids:
        user_rows = session.exec(select(User).where(User.id.in_(participant_ids))).all()
        users = {u.id: u for u in user_rows}

    def to_participant_user(uid: uuid.UUID | None) -> ParticipantUser | None:
        if uid is None or uid not in users:
            return None
        u = users[uid]
        return ParticipantUser(id=u.id, username=u.username, display_name=u.display_name)

    rounds: dict[int, list[MatchPublic]] = {}
    for match in matches:
        match_public = MatchPublic.model_validate(match)
        match_public.participant_1_user = to_participant_user(match.participant_1)
        match_public.participant_2_user = to_participant_user(match.participant_2)
        match_public.winner_user = to_participant_user(match.winner_id)
        rounds.setdefault(match.round, []).append(match_public)

    return BracketPublic(
        tournament_id=tournament_id,
        rounds=[RoundPublic(round=r, matches=m) for r, m in sorted(rounds.items())],
    )
