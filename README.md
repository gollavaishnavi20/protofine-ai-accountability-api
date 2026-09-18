# Protofine AI Accountability Receipt API

A backend system that stores AI request-response records and generates
tamper-evident hash-chain receipts.

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

Therefore, changing stored content without updating its hash causes
verification to fail.

## API Endpoints

### POST /records

Stores an AI request-response pair and creates a hash-chain receipt.

Example request:

```json
{
  "ai_request": "What is the capital of France?",
  "ai_response": "The capital of France is Paris."
}