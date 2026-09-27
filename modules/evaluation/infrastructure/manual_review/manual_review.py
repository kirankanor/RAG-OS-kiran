from __future__ import annotations
from datetime import UTC, datetime
from shared.infrastructure.database.db_models import RatingRow, get_session


def save_rating(run_id: str, query: str, thumbs_up: bool, note: str = "") -> None:
    row = RatingRow(run_id=run_id, query=query, thumbs_up=thumbs_up, note=note,
                     created_at=datetime.now(UTC).isoformat())
    with get_session() as session:
        session.add(row)
        session.commit()


def ratings_for_run(run_id: str) -> list[RatingRow]:
    from sqlmodel import select
    with get_session() as session:
        return list(session.exec(select(RatingRow).where(RatingRow.run_id == run_id)))


def run_score_summary(run_id: str) -> dict[str, int]:
    ratings = ratings_for_run(run_id)
    up = sum(1 for r in ratings if r.thumbs_up)
    down = sum(1 for r in ratings if not r.thumbs_up)
    return {"thumbs_up": up, "thumbs_down": down, "total": up + down}
