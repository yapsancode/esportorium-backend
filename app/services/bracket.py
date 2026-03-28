import uuid
from datetime import datetime, timezone

from sqlmodel import Session, func, select

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


def advance_winner(match: Match, session: Session) -> Match | None:
    """
    Seed the winner of a completed match into the appropriate slot of the next-round
    match. Creates that match if it doesn't exist yet. Returns None when the completed
    match was the grand final (only match in its round).
    """
    round_match_count = session.exec(
        select(func.count(Match.id)).where(
            Match.tournament_id == match.tournament_id,
            Match.round == match.round,
        )
    ).one()

    if round_match_count == 1:
        # Grand final — nothing to advance to.
        return None

    next_round = match.round + 1
    next_match_number = (match.match_number + 1) // 2
    fills_slot_1 = match.match_number % 2 == 1

    next_match = session.exec(
        select(Match).where(
            Match.tournament_id == match.tournament_id,
            Match.round == next_round,
            Match.match_number == next_match_number,
        )
    ).first()

    if next_match is None:
        next_match = Match(
            tournament_id=match.tournament_id,
            round=next_round,
            match_number=next_match_number,
        )
        session.add(next_match)

    if fills_slot_1:
        next_match.participant_1 = match.winner_id
    else:
        next_match.participant_2 = match.winner_id

    next_match.updated_at = datetime.now(timezone.utc)
    session.add(next_match)
    session.commit()
    session.refresh(next_match)
    return next_match
