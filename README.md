# Protofine AI Accountability Receipt API

A backend system that stores AI request-response records and generates tamper-evident hash-chain receipts.

## Problem

AI outputs may need to be checked after they were generated.

This project records:

- What was sent to the AI
- What the AI returned
- When the record was created
- The hash of the record
- The hash of the previous record

Each record is linked to the previous record using a SHA-256 hash.

## How It Works

For the first record:

Previous Hash → Genesis Hash

For every later record:

Previous Hash → Hash of Previous Record

The record hash is calculated from:

- Record ID
- AI request
- AI response
- Previous hash
- Creation timestamp

Therefore, changing stored content without updating its hash causes verification to fail.

## API Endpoints

### POST /records

Stores an AI request-response pair and creates a hash-chain receipt.

Example request:

```json
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

GET /records

Returns the stored records and their hash-chain information.

GET /verify/{record_id}

Verifies whether a record is intact and whether its chain links remain valid.

Possible results:

- INTACT
- TAMPERED
- CHAIN_BROKEN

Tampering Demonstration

The system was tested by directly changing the stored AI response of an existing record without changing its stored hash.

Original response:

The capital of France is Paris.

Tampered response:

The capital of France is London.

The verification endpoint detected the modification and returned:

{
  "record_id": 1,
  "valid": false,
  "status": "TAMPERED"
}

A later record that depends on the altered record can also detect that the hash chain has been broken.

What the Receipt Proves

The receipt provides evidence that:

- The stored record matches the content used to generate its hash.
- The hash-chain links are consistent.
- A modification to stored content can be detected during verification.

What the Receipt Does Not Prove

The receipt does not prove that the original AI response was:

- Truthful
- Correct
- Unbiased

It only provides tamper-evident integrity for the recorded data.

It does not provide cryptographic proof of who originally created the record because this implementation does not use digital signatures or real signing keys.

Technology

- Python
- FastAPI
- SQLite
- SHA-256
- Pydantic
- Uvicorn

Project Structure

protofine-backend-task/
├── main.py
├── database.py
├── hash_chain.py
├── models.py
├── requirements.txt
├── README.md
└── .gitignore

The receipts.db database file is generated automatically when the application runs and is not committed to the repository.

Running the Project

Create and activate a virtual environment:

python -m venv venv
.\venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Start the API:

uvicorn main:app --reload

Open the API documentation:

http://127.0.0.1:8000/docs

Key Design Decision

The implementation uses a hash chain rather than isolated hashes.

Each record stores the hash of the previous record. This means an unauthorized modification to an earlier record can also be detected when verifying a later record because the chain link no longer matches.

The implementation intentionally avoids accounts, authentication, external signing keys, and unnecessary infrastructure because the core requirement is demonstrating verifiable AI-record integrity.

Limitations

This is a small demonstration system focused on tamper detection.

It does not provide:

- User authentication
- Digital signatures
- External trusted timestamping
- Distributed storage

The system demonstrates integrity checking of the stored records and hash-chain relationships.

Failure Test

After a valid AI request-response record was created, the stored AI response was manually changed without recalculating its hash.

The verification endpoint detected the mismatch and reported the record as TAMPERED.

This demonstrates the main purpose of the system: making stored AI outputs verifiable after the fact.
