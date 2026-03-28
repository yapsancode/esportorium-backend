import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_min_role
from app.models.tournament import Tournament
from app.models.user import User, UserRole
from app.schemas.tournament import TournamentCreate, TournamentPublic, TournamentUpdate

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.post("", response_model=TournamentPublic, status_code=status.HTTP_201_CREATED)
def create_tournament(
    data: TournamentCreate,
    current_user: Annotated[User, Depends(require_min_role(UserRole.organizer))],
    session: Annotated[Session, Depends(get_session)],
) -> Tournament:
    tournament = Tournament(**data.model_dump(), organizer_id=current_user.id)
    session.add(tournament)
    session.commit()
    session.refresh(tournament)
    return tournament


@router.get("", response_model=list[TournamentPublic])
def list_tournaments(
    session: Annotated[Session, Depends(get_session)],
) -> list[Tournament]:
    return session.exec(select(Tournament)).all()


@router.get("/{tournament_id}", response_model=TournamentPublic)
def get_tournament(
    tournament_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
) -> Tournament:
    tournament = session.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    return tournament


@router.patch("/{tournament_id}", response_model=TournamentPublic)
def update_tournament(
    tournament_id: uuid.UUID,
    data: TournamentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Tournament:
    tournament = session.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if tournament.organizer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this tournament")

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(tournament, field, value)
    tournament.updated_at = datetime.now(timezone.utc)

    session.add(tournament)
    session.commit()
    session.refresh(tournament)
    return tournament


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament(
    tournament_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    tournament = session.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if tournament.organizer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this tournament")

    session.delete(tournament)
    session.commit()
