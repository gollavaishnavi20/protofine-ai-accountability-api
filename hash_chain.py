import hashlib
import json


GENESIS_HASH = "0" * 64


def canonical_json(data):
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":")
    )


def calculate_record_hash(
    record_id,
    ai_request,
    ai_response,
    previous_hash,
    created_at
):
    data = {
        "id": record_id,
        "ai_request": ai_request,
        "ai_response": ai_response,
        "previous_hash": previous_hash,
        "created_at": created_at
    }

    content = canonical_json(data)

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()