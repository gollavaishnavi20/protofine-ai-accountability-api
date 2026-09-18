from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from database import (
    initialize_database,
    get_last_record,
    insert_record,
    update_record_hash,
    get_record,
    get_previous_record,
    get_all_records,
)

from hash_chain import (
    GENESIS_HASH,
    calculate_record_hash,
)

from models import (
    AIRecordRequest,
    ReceiptResponse,
    VerificationResponse,
)


app = FastAPI(
    title="Protofine AI Accountability Receipt API",
    description=(
        "A backend system that stores AI request-response records "
        "and generates hash-chain receipts to detect tampering."
    ),
    version="1.0.0",
)


# Create the database table when the application starts.
initialize_database()


@app.get("/")
def root():
    return {
        "message": "Protofine AI Accountability Receipt API",
        "status": "running",
    }


@app.post(
    "/records",
    response_model=ReceiptResponse,
)
def create_record(record: AIRecordRequest):
    """
    Store an AI request and response and generate
    a cryptographic receipt linked to the previous record.
    """

    # Find the latest record in the chain.
    last_record = get_last_record()

    if last_record:
        previous_hash = last_record["record_hash"]
    else:
        previous_hash = GENESIS_HASH

    # Generate a UTC timestamp.
    created_at = datetime.now(timezone.utc).isoformat()

    # Insert the record first so SQLite can generate its ID.
    # The final hash is calculated immediately afterward using
    # the real database-generated ID.
    temporary_hash = GENESIS_HASH

    record_id = insert_record(
        ai_request=record.ai_request,
        ai_response=record.ai_response,
        previous_hash=previous_hash,
        record_hash=temporary_hash,
        created_at=created_at,
    )

    # Calculate the final cryptographic hash using
    # the actual record ID and all important record data.
    final_hash = calculate_record_hash(
        record_id=record_id,
        ai_request=record.ai_request,
        ai_response=record.ai_response,
        previous_hash=previous_hash,
        created_at=created_at,
    )

    # Store the final hash.
    update_record_hash(
        record_id=record_id,
        record_hash=final_hash,
    )

    # Return the receipt to the client.
    return ReceiptResponse(
        record_id=record_id,
        receipt=final_hash,
        previous_hash=previous_hash,
        created_at=created_at,
    )


@app.get(
    "/records",
)
def list_records():
    """
    Return all stored AI records in chain order.
    """

    records = get_all_records()

    return {
        "count": len(records),
        "records": [
            {
                "id": record["id"],
                "ai_request": record["ai_request"],
                "ai_response": record["ai_response"],
                "previous_hash": record["previous_hash"],
                "record_hash": record["record_hash"],
                "created_at": record["created_at"],
            }
            for record in records
        ],
    }


@app.get(
    "/verify/{record_id}",
    response_model=VerificationResponse,
)
def verify_record(record_id: int):
    """
    Verify the integrity of a record and its position
    in the hash chain.
    """

    record = get_record(record_id)

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Record not found",
        )

    # ---------------------------------------------------------
    # 1. Recalculate the record's hash.
    # ---------------------------------------------------------

    expected_hash = calculate_record_hash(
        record_id=record["id"],
        ai_request=record["ai_request"],
        ai_response=record["ai_response"],
        previous_hash=record["previous_hash"],
        created_at=record["created_at"],
    )

    # If the recalculated hash differs from the stored hash,
    # something inside this record was changed.
    if expected_hash != record["record_hash"]:
        return VerificationResponse(
            record_id=record_id,
            valid=False,
            status="TAMPERED",
            reason=(
                "The record content no longer matches its stored hash. "
                "The AI request, AI response, timestamp, record ID, "
                "or previous-hash information may have been changed."
            ),
        )

    # ---------------------------------------------------------
    # 2. Verify the connection to the previous record.
    # ---------------------------------------------------------

    previous_record = get_previous_record(record_id)

    if previous_record:
        if record["previous_hash"] != previous_record["record_hash"]:
            return VerificationResponse(
                record_id=record_id,
                valid=False,
                status="CHAIN_BROKEN",
                reason=(
                    "The record's previous_hash does not match "
                    "the hash of the previous stored record."
                ),
            )

    else:
        # The first record must point to the genesis hash.
        if record["previous_hash"] != GENESIS_HASH:
            return VerificationResponse(
                record_id=record_id,
                valid=False,
                status="CHAIN_BROKEN",
                reason=(
                    "The first record does not point to the "
                    "expected genesis hash."
                ),
            )

    # ---------------------------------------------------------
    # 3. Walk backward through the chain.
    # ---------------------------------------------------------
    #
    # This ensures that verification of a later record can also
    # discover corruption in an earlier chain link.
    #

    current_record = record

    while True:
        previous_record = get_previous_record(current_record["id"])

        if not previous_record:
            # We reached the beginning of the chain.
            if current_record["previous_hash"] != GENESIS_HASH:
                return VerificationResponse(
                    record_id=record_id,
                    valid=False,
                    status="CHAIN_BROKEN",
                    reason=(
                        "The chain does not terminate at "
                        "the expected genesis hash."
                    ),
                )

            break

        # Verify the previous record's own content.
        previous_expected_hash = calculate_record_hash(
            record_id=previous_record["id"],
            ai_request=previous_record["ai_request"],
            ai_response=previous_record["ai_response"],
            previous_hash=previous_record["previous_hash"],
            created_at=previous_record["created_at"],
        )

        if previous_expected_hash != previous_record["record_hash"]:
            return VerificationResponse(
                record_id=record_id,
                valid=False,
                status="CHAIN_BROKEN",
                reason=(
                    f"Record {previous_record['id']} has been altered. "
                    "Its stored hash no longer matches its content."
                ),
            )

        # Verify that the current record correctly references
        # the previous record.
        if current_record["previous_hash"] != previous_record["record_hash"]:
            return VerificationResponse(
                record_id=record_id,
                valid=False,
                status="CHAIN_BROKEN",
                reason=(
                    f"The hash link between record "
                    f"{previous_record['id']} and record "
                    f"{current_record['id']} is broken."
                ),
            )

        current_record = previous_record

    # ---------------------------------------------------------
    # 4. Everything checked successfully.
    # ---------------------------------------------------------

    return VerificationResponse(
        record_id=record_id,
        valid=True,
        status="INTACT",
        reason=(
            "The record content matches its stored hash and "
            "the hash-chain links back correctly to the genesis hash."
        ),
    )