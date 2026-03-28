import math
import uuid

from sqlmodel import Session, select

from app.models.match import Match, MatchStatus
from app.models.registration import Registration, RegistrationStatus
from app.models.tournament import Tournament, TournamentFormat


def _next_power_of_two(n: int) -> int:
    return 1 << (n - 1).bit_length()


def generate_bracket(tournament_id: uuid.UUID, session: Session) -> list[Match]:
    tournament = session.get(Tournament, tournament_id)
    if tournament is None:
        raise ValueError("Tournament not found")
    if tournament.format != TournamentFormat.single_elimination:
        raise ValueError(f"Bracket generation not supported for format: {tournament.format.value}")

    confirmed = session.exec(
        select(Registration).where(
            Registration.tournament_id == tournament_id,
            Registration.status == RegistrationStatus.confirmed,
        )
    ).all()

    participant_ids: list[uuid.UUID | None] = [r.user_id for r in confirmed]
    n = len(participant_ids)

    if n < 2:
        raise ValueError("At least 2 confirmed registrations are required to generate a bracket")

    # Pad to the next power of two with None slots (byes).
    bracket_size = _next_power_of_two(n)
    participant_ids += [None] * (bracket_size - n)

    matches: list[Match] = []
    for match_number, i in enumerate(range(0, bracket_size, 2), start=1):
        p1 = participant_ids[i]
        p2 = participant_ids[i + 1]

        is_bye = p1 is None or p2 is None
        match = Match(
            tournament_id=tournament_id,
            round=1,
            match_number=match_number,
            participant_1=p1,
            participant_2=p2,
            winner_id=p1 if p2 is None else (p2 if p1 is None else None),
            status=MatchStatus.bye if is_bye else MatchStatus.pending,
        )
        session.add(match)
        matches.append(match)

    session.commit()
    for match in matches:
        session.refresh(match)

    return matches
