import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_min_role
from app.models.registration import Registration, RegistrationStatus
from app.models.tournament import Tournament, TournamentStatus
from app.models.user import User, UserRole
from app.schemas.registration import RegistrationPublic

router = APIRouter(prefix="/tournaments/{tournament_id}", tags=["registrations"])


def _get_open_tournament(tournament_id: uuid.UUID, session: Session) -> Tournament:
    tournament = session.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if tournament.status != TournamentStatus.open:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tournament is not open for registration (status: {tournament.status.value})",
        )
    return tournament


@router.post("/register", response_model=RegistrationPublic, status_code=status.HTTP_201_CREATED)
def register_for_tournament(
    tournament_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Registration:
    tournament = _get_open_tournament(tournament_id, session)

    existing = session.exec(
        select(Registration).where(
            Registration.tournament_id == tournament_id,
            Registration.user_id == current_user.id,
        )
    ).first()

    if existing and existing.status != RegistrationStatus.cancelled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already registered for this tournament")

    active_count = session.exec(
        select(func.count(Registration.id)).where(
            Registration.tournament_id == tournament_id,
            Registration.status != RegistrationStatus.cancelled,
        )
    ).one()
    if active_count >= tournament.max_teams:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tournament is full")

    if existing:
        # Reuse the cancelled row instead of inserting a duplicate.
        existing.status = RegistrationStatus.pending
        existing.updated_at = datetime.now(timezone.utc)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    registration = Registration(tournament_id=tournament_id, user_id=current_user.id)
    session.add(registration)
    session.commit()
    session.refresh(registration)
    return registration


@router.get("/registrations", response_model=list[RegistrationPublic])
def list_registrations(
    tournament_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_min_role(UserRole.organizer))],
    session: Annotated[Session, Depends(get_session)],
) -> list[Registration]:
    tournament = session.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found")
    if tournament.organizer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this tournament")

    return session.exec(
        select(Registration).where(Registration.tournament_id == tournament_id)
    ).all()


@router.delete("/register", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_from_tournament(
    tournament_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    tournament = _get_open_tournament(tournament_id, session)

    registration = session.exec(
        select(Registration).where(
            Registration.tournament_id == tournament_id,
            Registration.user_id == current_user.id,
            Registration.status != RegistrationStatus.cancelled,
        )
    ).first()
    if not registration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active registration found")

    registration.status = RegistrationStatus.cancelled
    registration.updated_at = datetime.now(timezone.utc)
    session.add(registration)
    session.commit()
