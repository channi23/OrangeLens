# Pramāṇa MVP — BUILD.md
Protocol v0 | Local-first build → Azure deployment

Repository: OrangeLens/

============================================================
GLOBAL EXECUTION RULES (MANDATORY)
============================================================

1. Two-stage execution model
   - Stage A: LOCAL BUILD ONLY
   - Stage B: AZURE DEPLOYMENT ONLY
   - Stage B MUST NOT start unless explicitly approved by the human.

2. Local-first mandate
   - Every service must run locally first using Docker and local Postgres.
   - Cloud deployment must require only environment variable and secret changes.

3. Protocol authority
   - `Protocol/specs/protocol_v0.md` is the single source of truth.
   - Backend implementation must strictly follow the protocol spec.

4. Privacy guarantees
   - Never store raw user content in persistent storage.
   - Ledger is append-only and hash-based.

5. Stop checkpoints are mandatory
   - The agent must stop at defined checkpoints and wait for human confirmation.

============================================================
STAGE A — LOCAL MVP BUILD (DO NOT DEPLOY)
============================================================

Objective: Build a complete Pramāṇa protocol node locally (cryptographic proofs + ledger dedupe) AND ship an SDK that developers use as the only integration surface.

------------------------------------------------------------
A0 — Repository Groundwork
------------------------------------------------------------

A0.1 Repository structure (locked)
- Protocol/specs/   → protocol contracts
- api/              → FastAPI backend
- app/              → frontend / mobile app
- infra/            → Docker / compose
- sdks/             → SDKs (required for MVP)

A0.2 Local execution environment
- Docker
- Local PostgreSQL via Docker
- No cloud services

------------------------------------------------------------
A1 — Protocol Contract + Cryptographic Identity
------------------------------------------------------------

A1.1 Protocol specification
File: Protocol/specs/protocol_v0.md

Must define:
- VerificationRequest
- VerificationResult
- ProofPayload
- Hashing rules (canonicalization + sha256)
- Endpoints:
  - POST /verify
  - POST /prepare_verify
  - GET /truth_record/by_hash/{hash}
  - GET /node/metadata
- Node identity (node_id + Ed25519 public key)
- Proof attachment strategy
- Non-blocking publishing stance

A1.2 Backend schemas
File: api/models/schemas.py

Models:
- VerificationRequest
- VerificationResult
- ProofPayload
- NodeMetaData
- Citation

A1.3 Node identity endpoint
Endpoint:
- GET /node/metadata

Returns:
- node_id
- node_name
- node_version
- region
- capabilities
- public_key (Ed25519)

A1.4 Cryptographic proof system
- Generate or load Ed25519 private key (BASE64)
- Load key at application startup
- Derive public key in memory
- Implement:
  - sign_proof(payload) → compact proof string
  - verify_proof(proof, public_key)

Local test endpoint:
- GET /node/test_sign

A1.5 Proof attachment strategy
- Protocol never blocks publishing
- Proof is attached as metadata

Supported attachment methods:
- HTTP header: X-Pramana-Proof
- JSON field: pramana_proof
- HTML meta tag

Proof may be:
- inline (compact proof)
- referenced via URL
- or both

STOP CHECKPOINT A1
- /node/metadata works
- Proof signing and verification works
- Protocol spec locked

------------------------------------------------------------
A2 — Ledger Integration (Local PostgreSQL)
------------------------------------------------------------

A2.1 Database connection
File: api/db.py

- SQLAlchemy engine and session
- DATABASE_URL-based connection
- Local PostgreSQL via Docker

A2.2 Ledger module
File: api/ledger.py

Functions:
- get_record_by_hash(content_hash)
- insert_truth_record(record)

Rules:
- Append-only
- Deterministic inserts
- No updates
- No raw content storage

A2.3 Hashing utilities
File: api/hash_utils.py

Functions:
- canonicalize_text(text)
- sha256_hex(string)
- Media hashing placeholders

A2.4 /verify v0 (dedupe-first flow)
Endpoint:
- POST /verify

Flow:
1. Compute or validate content_hash
2. Query ledger by content_hash
   - HIT → return cached result + proof + cached=true
   - MISS → run verification → build result → sign proof → insert record → return cached=false
3. Proof must always be included

A2.5 Record retrieval endpoints
- GET /truth_record/by_hash/{content_hash}
- GET /truth_record/{record_id} (optional)

A2.6 Cached indicator
- cached: true | false
- UI text: “Verified previously (instant)”

STOP CHECKPOINT A2
- Ledger deduplication works
- Cached verification returns instantly
- Proof returned for both cached and new records

------------------------------------------------------------
A3 — Verification Pipeline (Local MVP Quality)
------------------------------------------------------------

A3.1 Text verification
File: api/verifiers/text.py

Outputs:
- verdict
- truth_score
- confidence
- explanation
- citations[]

A3.2 Image verification
File: api/verifiers/image.py

Minimal checks:
- caption
- manipulation hints
- source checks

A3.3 Aggregation rules
File: api/scoring.py

- Deterministic aggregation
- Stable verdict_hash

A3.4 Evidence rules
- No raw content storage
- Citations limited to title + url


STOP CHECKPOINT A3 (END OF LOCAL MVP)
- /verify produces credible results
- Ledger, proof, and caching work end-to-end

------------------------------------------------------------
A4 — Pre-Verification Flow + Multi-Node (Docker) MVP
------------------------------------------------------------

Objective:
Demonstrate Pramāṇa as a "pre-verification" layer that can be integrated ONLY by website/platform developers via SDK. The content is verified during the publish flow and uploaded with a proof tag (metadata). This stage implements a service-based multi-node architecture using Docker (NOT P2P yet).

A4.1 Integration flow (SDK-only)
- External developers MUST integrate Pramāṇa via official SDKs.
- Direct HTTP calls to Pramāṇa endpoints are NOT considered a supported integration path for MVP.
- The SDK is the single integration surface; internally it calls Pramāṇa backend endpoints.

Example publish flow ("X" style platform):
1) User composes a post (text/image/video)
2) On "Post", the platform calls the Pramāṇa SDK (e.g., `sdk.verify(...)` or `sdk.prepareVerify(...)` + `sdk.verify(...)`)
3) The SDK calls Pramāṇa backend endpoints and returns `VerificationResult` + `proof` (compact) and/or `proof_url`
4) Platform publishes the content normally (Pramāṇa never blocks posting)
5) Platform attaches proof metadata to the published content:
   - HTTP header: `X-Pramana-Proof`
   - JSON field: `pramana_proof`
   - HTML meta tag: `<meta name="pramana-proof" ...>`

A4.2 Local multi-node architecture (Docker, service-based)
Node model:
- Service-based nodes in separate Docker containers
- Real HTTP calls between containers
- One Gateway/Aggregator Node orchestrates verifier nodes
- Ledger remains the backend persistence layer
- P2P discovery and networking is explicitly out of scope for MVP (future Phase 6+)

Minimum node set (3 nodes):
1) Gateway / Aggregator Node (public entrypoint)
   - Receives `/verify` requests
   - Computes/validates content_hash
   - Checks ledger for cache hit
   - Dispatches tasks to verifier nodes in parallel
   - Aggregates partial results deterministically
   - Produces final `VerificationResult`
   - Signs proof (Ed25519)
   - Writes append-only TruthRecord to Postgres ledger

2) Text Verifier Node
   - Implements text verification logic
   - Exposes `POST /node/verify_task` returning a partial result

3) Media Verifier Node (image/video placeholder)
   - Implements image verification MVP (and a video placeholder)
   - Exposes `POST /node/verify_task` returning a partial result

A4.3 Node contracts (MVP)
Each node MUST expose:
- `GET /node/metadata`
- `GET /node/health`

Verifier nodes MUST also expose:
- `POST /node/verify_task`

Gateway-to-verifier calls (Docker DNS):
- `http://verifier-text:8080/node/verify_task`
- `http://verifier-media:8080/node/verify_task`

A4.4 Registry (MVP)
- Use a static YAML registry: `api/config/nodes.yaml`
- Gateway reads this file on startup to find verifier URLs

A4.5 Docker Compose
- Create `docker-compose.yml` at repo root defining:
  - `gateway`
  - `verifier-text`
  - `verifier-media`
  - `postgres`
- Each service runs FastAPI on port 8080 internally
- Gateway is exposed to host (e.g., 8000)

STOP CHECKPOINT A4
- `docker compose up` starts all 4 services
- Gateway `/verify` fans out to both verifier nodes
- Ledger dedupe works (second call is cached)
- Proof is returned for both cached and new results
- Demo shows "publish with proof tag" (non-blocking)

------------------------------------------------------------
A5 — SDKs (MVP Required)
------------------------------------------------------------

Objective:
Provide an official developer SDK that is the ONLY supported integration method. Developers install the SDK via a package manager (npm) and call SDK functions; the SDK handles hashing, calling Pramāṇa endpoints, and returning structured results.

A5.1 Create JavaScript/TypeScript SDK package
Path:
- `sdks/pramana-js`

Package requirements:
- TypeScript-first
- Exports a client that accepts a base URL (local gateway URL during Stage A)
- Stable function signatures

A5.2 SDK functions (minimum MVP)
The SDK MUST expose:
- `computeContentHash(input)`
  - text canonicalization + sha256 for text
  - placeholder for media hashing
- `prepareVerify(request)`
  - wraps backend `POST /prepare_verify`
- `verify(request)`
  - wraps backend `POST /verify`
- `getRecordByHash(hash)`
  - wraps backend `GET /truth_record/by_hash/{hash}`

A5.3 Proof attachment helpers (SDK)
The SDK MUST provide helpers:
- `attachProofToHeaders(headers, proofResult)`
- `attachProofToPostObject(post, proofResult)`
- `attachProofToHTMLMeta(existingHtml, proofResult)` (simple string helper is sufficient)

A5.4 SDK packaging (local install)
- Ensure `package.json` supports building and local installation.
- Provide a minimal README in `sdks/pramana-js/README.md` showing:
  - install steps (local link / npm)
  - example usage `sdk.verify(...)`
  - how to attach proof to a post payload

A5.5 Local SDK smoke test
- Add a minimal Node script under `sdks/pramana-js/examples/quickstart.ts` (or .js) that:
  - calls `sdk.verify(...)` against the local gateway
  - prints `cached` and `proof`

STOP CHECKPOINT A5
- SDK can be installed locally (npm link or workspace)
- `sdk.verify(...)` works against local gateway
- Developer can attach proof using SDK helper methods

============================================================
STAGE B — AZURE DEPLOYMENT (ONLY AFTER APPROVAL)
============================================================

IMPORTANT:
- This stage must not start unless explicitly approved by the human.

------------------------------------------------------------
B0 — Azure setup (human-led)
------------------------------------------------------------
- Create Azure Resource Group
- Create Azure PostgreSQL Flexible Server
- Create Azure Container Apps environment
- Decide AI provider (Azure OpenAI or equivalent)

------------------------------------------------------------
B1 — Backend deployment
------------------------------------------------------------
- Build Docker images
- Deploy backend to Azure Container Apps
- Configure environment variables:
  - DATABASE_URL
  - PRAMANA_NODE_PRIVATE_KEY_B64
  - AI API keys

------------------------------------------------------------
B2 — Database migration
------------------------------------------------------------
- Create truth_records table in Azure PostgreSQL
- Validate schema parity with local DB

------------------------------------------------------------
B3 — Secrets management
------------------------------------------------------------
- Store secrets in Azure Key Vault
- Optional managed identity wiring

------------------------------------------------------------
B4 — Observability
------------------------------------------------------------
- Enable logs and metrics
- Track cache hit rate, latency, and error rate
- Do not log raw content

------------------------------------------------------------
B5 — Demo validation
------------------------------------------------------------
- Verify new content
- Verify same content again (cached)
- Proof attached to published content
- Proof verified via public key and truth_record endpoint

============================================================
END OF BUILD.md
============================================================