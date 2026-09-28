import hashlib
import json


def derive_seed(*parts: object) -> int:
    """Turn JSON-like parts into a seed that's identical in every process.

    Uses hashlib rather than the built-in hash(), which is randomized per
    process (ADR 0004).
    """
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return int.from_bytes(hashlib.sha256(payload.encode()).digest()[:8], "big")
