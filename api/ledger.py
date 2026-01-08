from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, String, func, JSON, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.db import Base


class TruthRecord(Base):
    __tablename__ = "truth_records"

    record_id = Column(String, primary_key=True, index=True)
    content_hash = Column(String, unique=True, index=True, nullable=False)
    result_json = Column(JSON, nullable=False)
    proof = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


def get_record_by_hash(db: Session, content_hash: str) -> Optional[TruthRecord]:
    stmt = select(TruthRecord).where(TruthRecord.content_hash == content_hash)
    return db.execute(stmt).scalar_one_or_none()


def get_record_by_id(db: Session, record_id: str) -> Optional[TruthRecord]:
    stmt = select(TruthRecord).where(TruthRecord.record_id == record_id)
    return db.execute(stmt).scalar_one_or_none()


def insert_truth_record(db: Session, record: Dict[str, Any]) -> TruthRecord:
    entry = TruthRecord(
        record_id=record["record_id"],
        content_hash=record["content_hash"],
        result_json=record["result_json"],
        proof=record["proof"],
    )
    db.add(entry)
    try:
        db.commit()
        db.refresh(entry)
        return entry
    except IntegrityError:
        db.rollback()
        existing = get_record_by_hash(db, record["content_hash"])
        if existing is None:
            raise
        return existing
