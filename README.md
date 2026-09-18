# Protofine AI Accountability Receipt API

A small backend API that stores AI request-response records and generates tamper-evident receipts using a SHA-256 hash chain.

## 1. Problem

AI outputs can be useful, but after an AI request and response are stored, it should be possible to check whether the stored record was changed later.

This project provides a simple way to:

- Store an AI request and its response
- Generate a receipt for the stored record
- Link each record to the previous record using a hash
- Verify whether a record has been modified
- Detect when an earlier record breaks the integrity of the chain

The implementation is intentionally small and uses SQLite instead of adding unnecessary infrastructure.

## 2. How It Works

Each stored record contains:

- AI request
- AI response
- Record ID
- Creation timestamp
- Previous record hash
- Current record hash

The current record hash is calculated using SHA-256 from the record's important fields.

The hash chain works like this:

Record 1 → Record 2 → Record 3 → Record 4

Each record stores the hash of the previous record.

If someone changes the stored contents of an earlier record, its recalculated hash will no longer match the stored hash.

The verification endpoint can then report that the record has been tampered with or that the chain is broken.

## 3. API Endpoints

### POST /records

Stores an AI request and AI response and returns a receipt.

Example request:

    {
      "ai_request": "What is the capital of France?",
      "ai_response": "The capital of France is Paris."
    }

Example response:

    {
      "record_id": 1,
      "receipt": "generated_sha256_hash",
      "previous_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "created_at": "timestamp"
    }

The receipt is the SHA-256 hash of the record contents together with the previous hash.

### GET /records

Returns the stored records.

This endpoint is useful for inspecting the current state of the database and seeing the hash-chain relationships between records.

### GET /verify/{record_id}

Verifies whether a stored record is intact and whether its hash-chain links are valid.

Example:

    GET /verify/1

A valid record returns a response similar to:

    {
      "record_id": 1,
      "valid": true,
      "status": "INTACT",
      "reason": "The record content matches its stored hash and the hash-chain links back correctly to the genesis hash."
    }

If the record has been modified, the API returns:

    {
      "record_id": 1,
      "valid": false,
      "status": "TAMPERED",
      "reason": "The record content no longer matches its stored hash."
    }

If an earlier record in the chain has been modified, verification of a later record can return:

    {
      "record_id": 4,
      "valid": false,
      "status": "CHAIN_BROKEN",
      "reason": "An earlier record in the hash chain has been altered."
    }

## 4. Tampering Demonstration

To demonstrate the integrity check, an existing database record was intentionally modified directly.

For example, the original response stored for Record 1 was:

    The capital of France is Paris.

The stored response was then intentionally changed to:

    The capital of France is London.

The stored hash was not changed.

When /verify/1 was called again, the API recalculated the hash from the current stored data.

Because the recalculated hash was different from the stored hash, the API detected the modification and returned:

    status: TAMPERED

This demonstrates that the system can detect changes made to stored AI records after they were written.

A later record can also detect the broken chain because it depends on the hash of the earlier record.

## 5. Failure Test

The tampering test was performed intentionally to demonstrate a failure case.

Before tampering:

    Record 1 → INTACT

After changing the stored AI response:

    Record 1 → TAMPERED

When a later record that depends on the altered record is verified, the system can detect the broken hash-chain relationship:

    Record 4 → CHAIN_BROKEN

This shows that the system does not silently accept modified historical data.

Important limitation:

This test demonstrates storage integrity and tamper detection. It does not prove that the AI's original answer was factually correct.

## 6. What the Receipt Proves

The receipt provides evidence that:

- The stored request and response match the data used to generate the hash.
- The record is linked to the previous record through the hash chain.
- Changes to the stored record can be detected.
- Changes to an earlier record can break the chain and be detected when later records are verified.

## 7. What the Receipt Does NOT Prove

The receipt does not prove:

- That the AI response was factually correct.
- That the AI model itself was trustworthy.
- Who originally created the AI request.
- Who has access to the database.
- That the database cannot be deleted.
- That the receipt is a cryptographic digital signature.
- That the original AI system cannot be compromised.

The receipt is primarily an integrity and tamper-evidence mechanism.

## 8. How the Hash Chain Works

The first record uses a fixed genesis hash:

    0000000000000000000000000000000000000000000000000000000000000000

For every new record:

    current_hash = SHA256(record_data + previous_hash)

The next record stores the previous record's hash.

For example:

    Record 1
    previous_hash = GENESIS_HASH
    record_hash = HASH_1

    Record 2
    previous_hash = HASH_1
    record_hash = HASH_2

    Record 3
    previous_hash = HASH_2
    record_hash = HASH_3

This creates a linked sequence of records.

If Record 1 changes, HASH_1 is no longer correct.

Record 2 still contains the old HASH_1, so the relationship between Record 1 and Record 2 becomes invalid.

## 9. How Verification Works

The verification endpoint performs two main checks.

### Check 1: Record integrity

The API recalculates the SHA-256 hash from the stored record data.

It compares the calculated hash with the stored hash.

If they are different:

    TAMPERED

### Check 2: Chain integrity

The API checks that the record's previous_hash matches the actual hash of the previous record.

It also walks backward through earlier records and checks their hashes.

If an earlier record has been modified:

    CHAIN_BROKEN

If all checks pass:

    INTACT

## 10. How It Holds as Records Grow

The system does not require a completely new mechanism for every additional record.

Each new record only needs:

- Its own data
- The previous record's hash
- Its newly calculated hash

Therefore, the chain can continue as:

    Record 1 → Record 2 → Record 3 → ... → Record N

The implementation uses SQLite, which is sufficient for this small demonstration.

For a production system with a large number of records, verification could be optimized further using checkpoints, indexed storage, external append-only logs, or stronger signing mechanisms.

## 11. Key Design Decisions

### SQLite

SQLite was selected because the task is intentionally small and does not require a separate database server.

It keeps the project easy to run and understand.

### SHA-256

SHA-256 provides a deterministic hash for the record contents.

If the input changes, the resulting hash changes.

### Hash Chain

A hash chain was used instead of hashing each record independently.

This means records are connected to their history, allowing changes to earlier records to affect later verification.

### No User Accounts

User accounts were intentionally not added because they are not required for the task.

### No Real Signing Keys

Digital signatures and key management were not added because the task specifically focuses on a small tamper-evident receipt system.

## 12. Technology Stack

- Python
- FastAPI
- SQLite
- Pydantic
- SHA-256
- Uvicorn

## 13. Project Structure

    protofine-backend-task/
    │
    ├── main.py
    ├── database.py
    ├── hash_chain.py
    ├── models.py
    ├── requirements.txt
    ├── README.md
    ├── .gitignore
    └── receipts.db

Note: receipts.db is generated automatically when the application runs and is excluded from Git using .gitignore.

## 14. Running the Project

Create and activate a virtual environment:

    python -m venv venv

    .\venv\Scripts\Activate.ps1

Install dependencies:

    pip install -r requirements.txt

Start the API:

    uvicorn main:app --reload

Open the interactive API documentation:

    http://127.0.0.1:8000/docs

The FastAPI Swagger interface can be used to create records and verify them.

## 15. Example Workflow

The intended workflow is:

    1. Send an AI request and response to POST /records.
    2. Receive the generated receipt.
    3. Create additional records.
    4. Use GET /verify/{record_id} to confirm integrity.
    5. Intentionally modify a stored record.
    6. Run verification again.
    7. Observe TAMPERED or CHAIN_BROKEN.

This provides a simple demonstration of how AI outputs can be stored with evidence of later modification.

## 16. Limitations

This project is a small proof-of-concept implementation.

It does not provide:

- Authentication
- Authorization
- Distributed storage
- Digital signatures
- Key management
- Immutable external storage
- Protection against deletion of the entire database
- Proof that an AI response is factually correct

The system focuses specifically on detecting modifications to stored records.

## 17. Conclusion

Protofine AI Accountability Receipt API demonstrates a lightweight approach to making stored AI outputs tamper-evident.

The system records the AI request and response, creates a SHA-256 receipt, links records through a hash chain, and verifies whether the stored data and chain remain intact.

The intentional tampering test demonstrates the main purpose of the system: if stored AI output is changed after being written, the verification process can detect the change instead of silently treating the modified record as original.
