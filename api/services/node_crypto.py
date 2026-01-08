import base64
import json
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


# Globals cached in-memory once at startup
_NODE_PRIVATE_KEY: Optional[Ed25519PrivateKey] = None
_NODE_PUBLIC_KEY: Optional[Ed25519PublicKey] = None
_NODE_PUBLIC_KEY_B64: str = ""


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)


def canonical_json(payload: Dict[str, Any]) -> bytes:
    """
    Deterministic JSON serialization for signing.
    This is critical so every node signs the exact same bytes.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_node_keys_from_b64(private_key_b64: str) -> None:
    """
    Load Ed25519 private key from BASE64 (raw 32 bytes).
    Derive public key and cache both globally.
    """
    global _NODE_PRIVATE_KEY, _NODE_PUBLIC_KEY, _NODE_PUBLIC_KEY_B64

    raw = base64.b64decode(private_key_b64)
    if len(raw) != 32:
        raise ValueError("Ed25519 private key must decode to 32 bytes (raw seed)")

    _NODE_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(raw)
    _NODE_PUBLIC_KEY = _NODE_PRIVATE_KEY.public_key()

    pub_raw = _NODE_PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    _NODE_PUBLIC_KEY_B64 = base64.b64encode(pub_raw).decode("utf-8")


def generate_node_private_key_b64() -> str:
    """
    Generate a new Ed25519 private key seed (32 bytes) and return base64.
    Use this once and store in Secret Manager or env.
    """
    priv = Ed25519PrivateKey.generate()
    raw = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return base64.b64encode(raw).decode("utf-8")


def get_public_key_b64() -> str:
    return _NODE_PUBLIC_KEY_B64


def sign_proof(payload: Dict[str, Any]) -> str:
    """
    sign_proof(payload) -> compact string

    Format (simple, MVP):
      pramana.v0.<payload_b64url>.<sig_b64url>

    Where:
      payload_b64url = base64url(canonical_json(payload))
      sig_b64url     = base64url(Ed25519Sign(payload_bytes))
    """
    if _NODE_PRIVATE_KEY is None:
        raise RuntimeError("Node private key not loaded")

    payload_bytes = canonical_json(payload)
    sig = _NODE_PRIVATE_KEY.sign(payload_bytes)

    token = "pramana.v0." + _b64url_encode(payload_bytes) + "." + _b64url_encode(sig)
    return token


def verify_proof(compact: str, public_key_b64: str) -> Dict[str, Any]:
    """
    verify_proof(proof, public_key) helper for tests

    Returns the decoded payload dict if valid, else raises ValueError.
    """
    parts = compact.split(".")
    if len(parts) != 4 or parts[0] != "pramana" or parts[1] != "v0":
        raise ValueError("Invalid proof format")

    payload_b = _b64url_decode(parts[2])
    sig_b = _b64url_decode(parts[3])

    pub_raw = base64.b64decode(public_key_b64)
    if len(pub_raw) != 32:
        raise ValueError("Ed25519 public key must decode to 32 bytes")

    pub = Ed25519PublicKey.from_public_bytes(pub_raw)

    try:
        pub.verify(sig_b, payload_b)
    except Exception:
        raise ValueError("Signature verification failed")

    return json.loads(payload_b.decode("utf-8"))