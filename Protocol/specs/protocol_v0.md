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

### POST /prepare_verify
Input: VerificationRequest
Output: { content_hash: string }

Rules:
- Compute content_hash from canonicalized content
- Return content_hash without running verification

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
- node_name
- node_version
- region
- capabilities
- public_key (Ed25519)
- protocol_version

## Proof Attachment Strategy 

### 1) Non-Blocking Stance
- Pramāṇa never prevents publishing.
- If verification fails or times out, the content still posts.
- The post may be tagged as unverified (no proof attached) or pending proof.

### 2) Attachment Options
A publisher MAY attach:
- proof (compact signed string), OR
- proof_url (link to a truth record endpoint), OR
- both

### 3) Verification time constraint
- The attach mechanism must be fast.
The verification can be:
- synchronous (fast mode, immediate proof)
- asynchronous (post first, attach proof later)

### 4) Proof Representation

A proof may be represented in one of two ways:

- pramana_proof: a compact signed proof string produced by the node
- pramana_proof_url: a URL that resolves to the verification record or proof payload

If the compact proof size is small enough for inline transport, `pramana_proof` SHOULD be attached directly.
If the proof is large or verification is asynchronous, `pramana_proof_url` SHOULD be attached instead.
Both fields MAY be attached together.

### 5) Recommended Attachment Patterns

The Pramāṇa Protocol recommends the following attachment patterns for interoperability across platforms.

A) HTTP Header Attachment
Best suited for API gateways, upload proxies, and backend services.

Recommended headers:
- X-Pramana-Proof: <compact-proof-string>
- X-Pramana-Proof-URL: <truth-record-url> (optional)
- X-Pramana-Node: <node_id> (optional)

B) JSON Field Attachment
Best suited for mobile apps, SDK integrations, and structured post objects.

Example:
{
  "content": "...",
  "media_url": "...",
  "pramana_proof": "pramana.v0.<payload>.<signature>",
  "pramana_proof_url": "https://<gateway>/truth_record/by_hash/<content_hash>"
}

C) HTML Meta Tag Attachment
Best suited for websites, blogs, and public articles.

Example:
<meta name="pramana-proof" content="pramana.v0.<payload>.<signature>">
<meta name="pramana-proof-url" content="https://<gateway>/truth_record/by_hash/<content_hash>">

### 6) Verification Responsibility

Verification of a Pramāṇa proof is the responsibility of the consumer or platform.

Any verifier MAY:
- fetch node metadata via /node/metadata
- retrieve the public key of the issuing node
- validate the signature over the proof payload
- independently assess trust based on verdict, issuer, and timestamp

Pramāṇa nodes do not enforce policy decisions. They only provide signed verification records.
