from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class ContentType(str, Enum):
    text = "text"
    image = "image"
    video = "video"
    url = "url"


class Verdict(str, Enum):
    true = "true"
    misleading = "misleading"
    unknown = "unknown"
    unverified = "unverified"


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Citation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    url: Optional[HttpUrl] = None


class NodeMetaData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    node_id: str = Field(..., min_length=1)
    node_name: Optional[str] = None
    node_version: Optional[str] = None
    region: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    public_key: Optional[str] = None


class VerificationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    content_type: ContentType
    text: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    media_url: Optional[HttpUrl] = None
    content_hash: Optional[str] = None
    client_id: Optional[str] = None


class ProofPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    protocol: str = Field(default="pramana-proof-v0")
    record_id: str
    content_hash: str
    verdict: Verdict
    truth_score: float = Field(..., ge=0.0, le=1.0)
    verdict_hash: str
    issued_at: datetime
    issuer: str


class VerificationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    record_id: str
    content_hash: str
    verdict: Verdict
    truth_score: float = Field(..., ge=0.0, le=1.0)
    confidence: Confidence
    explanation: str
    citations: List[Citation] = Field(default_factory=list)
    issued_at: datetime
    issuer: str
    verdict_hash: str
    proof: str


# Backwards-compat alias for earlier typo usage (safe to remove later).
Verfication_Request = VerificationRequest






