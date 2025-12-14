# Pramāṇa Protocol v0

## Purpose
Pramāṇa is a pre-publish verification protocol. Publishing is never blocked. A signed Proof Record is attached to content as verifiable metadata.

## Core Objects

### 1) VerificationRequest
Used by clients/SDKs to request verification before publishing.

Fields:
- content_type: "text" | "image" | "video" | "url"
- text?: string
- source_url?: string
- media_url?: string (optional, if uploaded to storage)
- content_hash?: string (sha256 of canonical content)
- client_id?: string

### 2) VerificationResult
Returned by the protocol node.

Fields:
- record_id: string
- content_hash: string
- verdict: "true" | "misleading" | "unknown" | "unverified"
- truth_score: number (0..1)
- confidence: "low" | "medium" | "high"
- explanation: string
- citations: array of { title?: string, url?: string }
- issued_at: ISO timestamp
- issuer: string (node_id)
- verdict_hash: string
- proof: string (signed payload, compact)

### 3) ProofPayload (signed)
What is signed by the node and can be attached to published content.

payload:
- protocol: "pramana-proof-v0"
- record_id
- content_hash
- verdict
- truth_score
- verdict_hash
- issued_at
- issuer

signature:
- algorithm: Ed25519
- encoding: proof is a compact string containing payload + signature

## Hashing
- canonical_text(text):
  - trim whitespace
  - normalize multiple spaces to single space
- content_hash = sha256(canonical_text(text)) for text
- verdict_hash = sha256(stable_json({verdict, truth_score, issuer, issued_at}))

## API Endpoints

### POST /verify
Input: VerificationRequest
Output: VerificationResult

Rules:
- If ledger has content_hash: return cached result (same record/proof)
- Else: run verification -> create TruthRecord -> return result

### GET /truth_record/by_hash/{content_hash}
Returns the cached VerificationResult (or minimal record if configured)

### GET /node/metadata
Returns:
- node_id
- public_key (Ed25519)
- protocol_version