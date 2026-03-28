import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.dependencies import require_min_role
from app.models.draft import DraftEntry
from app.models.game import Game
from app.models.match import Match, MatchStatus
from app.models.tournament import Tournament
from app.models.user import User, UserRole
from app.schemas.game import DraftEntryPublic, GameCreate, GameWithDraftPublic
from app.services.bracket import advance_winner

router = APIRouter(prefix="/matches/{match_id}", tags=["games"])


def _build_game_response(game: Game, session: Session) -> GameWithDraftPublic:
    draft_entries = session.exec(
        select(DraftEntry).where(DraftEntry.game_id == game.id).order_by(DraftEntry.phase)
    ).all()
    return GameWithDraftPublic(
        **game.model_dump(),
        draft=[DraftEntryPublic.model_validate(e) for e in draft_entries],
    )


@router.post("/games", response_model=GameWithDraftPublic, status_code=status.HTTP_201_CREATED)
def record_game(
    match_id: uuid.UUID,
    data: GameCreate,
    current_user: Annotated[User, Depends(require_min_role(UserRole.organizer))],
    session: Annotated[Session, Depends(get_session)],
) -> GameWithDraftPublic:
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    tournament = session.get(Tournament, match.tournament_id)
    if tournament.organizer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this tournament")

    if match.status == MatchStatus.bye:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot record games for a bye match")
    if match.status == MatchStatus.completed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match series is already completed")

    valid_participants = {p for p in (match.participant_1, match.participant_2) if p is not None}
    if data.winner_id not in valid_participants:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="winner_id must be one of the match participants",
        )

    duplicate = session.exec(
        select(Game).where(Game.match_id == match_id, Game.game_number == data.game_number)
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Game number {data.game_number} has already been recorded for this match",
        )

    # Create the game record.
    game = Game(
        match_id=match_id,
        game_number=data.game_number,
        winner_id=data.winner_id,
        duration_minutes=data.duration_minutes,
    )
    session.add(game)
    session.flush()  # populate game.id before creating draft entries

    # Create draft entries.
    for entry in data.draft:
        session.add(DraftEntry(game_id=game.id, **entry.model_dump()))

    # Tally the win for the winning side.
    if data.winner_id == match.participant_1:
        match.team_1_wins += 1
    else:
        match.team_2_wins += 1

    # Mark the series as ongoing once the first game is recorded.
    if match.status == MatchStatus.pending:
        match.status = MatchStatus.ongoing

    # Check if a team has clinched the series.
    series_complete = False
    if match.team_1_wins >= match.games_to_win:
        match.winner_id = match.participant_1
        series_complete = True
    elif match.team_2_wins >= match.games_to_win:
        match.winner_id = match.participant_2
        series_complete = True

    if series_complete:
        match.status = MatchStatus.completed

    match.updated_at = datetime.now(timezone.utc)
    session.add(match)
    session.commit()
    session.refresh(game)

    if series_complete:
        advance_winner(match, session)

    return _build_game_response(game, session)


@router.get("/games", response_model=list[GameWithDraftPublic])
def list_games(
    match_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
) -> list[GameWithDraftPublic]:
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    games = session.exec(
        select(Game).where(Game.match_id == match_id).order_by(Game.game_number)
    ).all()

    return [_build_game_response(g, session) for g in games]
