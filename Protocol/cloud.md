

# Pramāṇa — Azure Deployment Guide (Stage B)
CLI-only | Agent-driven | Human-assisted only when required

Repository: OrangeLens  
Prerequisite: **Stage A (Local MVP) completed and validated**

---

## GLOBAL RULES (MANDATORY)

1. **CLI-only execution**
   - Do NOT use Azure Portal unless explicitly instructed.
   - All resources must be created using Azure CLI (`az`).

2. **Human interaction policy**
   - The agent MUST pause and prompt the human ONLY for:
     - `az login`
     - Supplying secret values (API keys, passwords)
   - All other steps must be executed autonomously by the agent.

3. **Cost safety**
   - Use lowest-cost SKUs only.
   - Do NOT remove Azure spending limits.
   - Prefer Basic / B1 / Consumption-tier resources.
   - Tear down resources when testing is complete.

4. **Architecture lock**
   - Deploy the same 3-node architecture validated in Stage A:
     - Gateway
     - Verifier-Text
     - Verifier-Media
   - No P2P networking in Stage B.

---

## STAGE B — AZURE BLOCKER CONTEXT SNAPSHOT

### Project & goal
- Project: Pramāṇa (repo: OrangeLens)
- Goal: Stage B Azure deployment of the same 3-node MVP (gateway + verifier-text + verifier-media) validated in Stage A, with Postgres ledger + signed proofs + SDK compatibility.

### Architecture
- 3 Container Apps:
  - pramana-gateway (external)
  - pramana-verifier-text (internal)
  - pramana-verifier-media (internal)
- Azure Container Apps environment: pramana-aca-env
- ACR: pramanaacr3038.azurecr.io
- Postgres Flexible Server: pramana-pg-23926 (DB: pramana, admin: pramana_admin)
- Gateway supports env-based discovery:
  - PRAMANA_VERIFIER_TEXT_URL
  - PRAMANA_VERIFIER_MEDIA_URL

### Stage A (Local MVP) — DONE & VERIFIED
- Multi-node Docker stack (gateway + verifier-text + verifier-media)
- Postgres ledger working; dedupe cached true/false verified
- Proof signing implemented
- SDK works locally
- All Stage A validation complete

### Stage B (Azure) — Current state
- Resource group: pramana-rg (region: centralindia)
- ACR: pramanaacr3038 (Basic, admin enabled)
- Container Apps:
  - pramana-gateway (external)
  - pramana-verifier-text (internal)
  - pramana-verifier-media (internal)
- Postgres Flexible Server: pramana-pg-23926 (DB: pramana)
- Images exist in ACR:
  - pramana-gateway:0.1
  - pramana-verifier-text:0.1
  - pramana-verifier-media:0.1
- Gateway endpoint not serving (`/node/metadata` times out/404) because image fails to pull

### Current blockers
- Container Apps cannot pull images from ACR: ImagePullUnauthorized persists for pramana-gateway (and later also for pramana-acr-pull-test) even when using ACR admin credentials.
- ACR itself is healthy; `az acr login` and `docker pull` succeed locally for all images.
- ACR image integrity is verified (tags + manifests exist).

### What has been tried (do not redo)
- ACR admin creds enabled; registry creds applied to Container Apps
- System-assigned MI + AcrPull
- User-assigned MI (pramana-acr-pull-uami) + AcrPull
- ACR ARM auth enabled; registry identity set to system or UAMI
- Re-setting image to force new revisions
- Full delete/recreate of all three Container Apps (gateway + verifiers)
- Gateway recreated with registry creds on create
- min-replicas=1 to force new revisions + logs
- Deactivated old failing revisions
- Secret re-set and password rotation
- Test app pramana-acr-pull-test created with same image + admin creds:
  - Initially looked OK, but once min replicas forced, it also showed ImagePullUnauthorized

### Current recommended next step
- Create an ACR token + scope map and use that token's credentials for registry auth in Container Apps (diagnostic and likely fix).
- Rationale: ACR admin creds work locally but Container Apps reject them; token auth is the next clean isolation path.

### Important names/values
- Resource Group: pramana-rg
- Region: centralindia
- ACR: pramanaacr3038 (login server pramanaacr3038.azurecr.io)
- ACA Env: pramana-aca-env
- Container Apps: pramana-gateway, pramana-verifier-text, pramana-verifier-media
- Test app: pramana-acr-pull-test (exists; currently failing pull)
- Postgres: pramana-pg-23926 (DB pramana, admin pramana_admin)
- Env vars:
  - DATABASE_URL (from PG)
  - PRAMANA_NODE_PRIVATE_KEY_B64
  - AI_API_KEY
  - PRAMANA_VERIFIER_TEXT_URL=http://pramana-verifier-text
  - PRAMANA_VERIFIER_MEDIA_URL=http://pramana-verifier-media

---

## REQUIRED HUMAN PREP (ONE-TIME)

### H1) Azure Login
The human must authenticate once:
```bash
az login
```

### H2) Create local secrets file (DO NOT COMMIT)
Create a file named:
```text
azure.secrets.env
```

With the following contents:
```bash
AI_API_KEY=PASTE_YOUR_AI_KEY_HERE
PRAMANA_NODE_PRIVATE_KEY_B64=PASTE_NODE_PRIVATE_KEY_B64
PG_ADMIN_PASSWORD=PASTE_STRONG_PASSWORD
```

Stop here. The agent will handle everything else.

---

## AGENT EXECUTION STARTS HERE

### B0 — Load secrets
```bash
set -a
source ./azure.secrets.env
set +a
```

---

## B1 — Define variables

```bash
RG="pramana-rg"
LOCATION="centralindia"
ENV="pramana-aca-env"

PG_SERVER="pramana-pg-$RANDOM"
PG_DB="pramana"
PG_ADMIN="pramana_admin"

ACR="pramanaacr$RANDOM"
IMG_TAG="0.1"
```

---

## B2 — Create Resource Group

```bash
az group create \
  --name "$RG" \
  --location "$LOCATION"
```

---

## B3 — Create Azure Container Registry (ACR)

```bash
az acr create \
  --resource-group "$RG" \
  --name "$ACR" \
  --sku Basic \
  --admin-enabled true

az acr login --name "$ACR"

REGISTRY="$ACR.azurecr.io"
```

---

## B4 — Build and Push Docker Images

> If separate Dockerfiles do not exist, reuse the same Dockerfile with different startup commands.

```bash
docker build -t "$REGISTRY/pramana-gateway:$IMG_TAG" -f api/Dockerfile .
docker push "$REGISTRY/pramana-gateway:$IMG_TAG"

docker build -t "$REGISTRY/pramana-verifier-text:$IMG_TAG" -f api/Dockerfile .
docker push "$REGISTRY/pramana-verifier-text:$IMG_TAG"

docker build -t "$REGISTRY/pramana-verifier-media:$IMG_TAG" -f api/Dockerfile .
docker push "$REGISTRY/pramana-verifier-media:$IMG_TAG"
```

---

## B5 — Create Container Apps Environment

```bash
az extension add --name containerapp --upgrade

az containerapp env create \
  --name "$ENV" \
  --resource-group "$RG" \
  --location "$LOCATION"
```

---

## B6 — Create PostgreSQL Flexible Server (Low Cost)

```bash
az postgres flexible-server create \
  --resource-group "$RG" \
  --name "$PG_SERVER" \
  --location "$LOCATION" \
  --admin-user "$PG_ADMIN" \
  --admin-password "$PG_ADMIN_PASSWORD" \
  --version 15 \
  --sku-name Standard_B1ms \
  --storage-size 32 \
  --public-access 0.0.0.0-255.255.255.255
```

Create database:
```bash
az postgres flexible-server db create \
  --resource-group "$RG" \
  --server-name "$PG_SERVER" \
  --database-name "$PG_DB"
```

Resolve host and build connection string:
```bash
PG_HOST=$(az postgres flexible-server show \
  -g "$RG" \
  -n "$PG_SERVER" \
  --query fullyQualifiedDomainName -o tsv)

DATABASE_URL="postgresql+psycopg2://$PG_ADMIN:$PG_ADMIN_PASSWORD@$PG_HOST:5432/$PG_DB?sslmode=require"
```

---

## B7 — Deploy Verifier Nodes (Internal Ingress)

### Verifier: Text
```bash
az containerapp create \
  --name pramana-verifier-text \
  --resource-group "$RG" \
  --environment "$ENV" \
  --image "$REGISTRY/pramana-verifier-text:$IMG_TAG" \
  --target-port 8080 \
  --ingress internal \
  --registry-server "$REGISTRY" \
  --secrets \
    db-url="$DATABASE_URL" \
    node-key="$PRAMANA_NODE_PRIVATE_KEY_B64" \
    ai-key="$AI_API_KEY" \
  --env-vars \
    DATABASE_URL=secretref:db-url \
    PRAMANA_NODE_PRIVATE_KEY_B64=secretref:node-key \
    AI_API_KEY=secretref:ai-key
```

### Verifier: Media
```bash
az containerapp create \
  --name pramana-verifier-media \
  --resource-group "$RG" \
  --environment "$ENV" \
  --image "$REGISTRY/pramana-verifier-media:$IMG_TAG" \
  --target-port 8080 \
  --ingress internal \
  --registry-server "$REGISTRY" \
  --secrets \
    db-url="$DATABASE_URL" \
    node-key="$PRAMANA_NODE_PRIVATE_KEY_B64" \
    ai-key="$AI_API_KEY" \
  --env-vars \
    DATABASE_URL=secretref:db-url \
    PRAMANA_NODE_PRIVATE_KEY_B64=secretref:node-key \
    AI_API_KEY=secretref:ai-key
```

---

## B8 — Deploy Gateway (External Ingress)

```bash
az containerapp create \
  --name pramana-gateway \
  --resource-group "$RG" \
  --environment "$ENV" \
  --image "$REGISTRY/pramana-gateway:$IMG_TAG" \
  --target-port 8080 \
  --ingress external \
  --registry-server "$REGISTRY" \
  --secrets \
    db-url="$DATABASE_URL" \
    node-key="$PRAMANA_NODE_PRIVATE_KEY_B64" \
    ai-key="$AI_API_KEY" \
  --env-vars \
    DATABASE_URL=secretref:db-url \
    PRAMANA_NODE_PRIVATE_KEY_B64=secretref:node-key \
    AI_API_KEY=secretref:ai-key \
    PRAMANA_VERIFIER_TEXT_URL="http://pramana-verifier-text" \
    PRAMANA_VERIFIER_MEDIA_URL="http://pramana-verifier-media"
```

---

## B9 — Validation

Resolve gateway URL:
```bash
GATEWAY_FQDN=$(az containerapp show \
  -g "$RG" \
  -n pramana-gateway \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Gateway URL: https://$GATEWAY_FQDN"
```

Test:
```bash
curl "https://$GATEWAY_FQDN/node/metadata"
```

Agent must confirm:
- `/node/metadata` returns valid node identity and public key
- `/verify` works via SDK
- Cache HIT/MISS behavior matches Stage A

---

## STAGE B TROUBLESHOOTING

### B10 — ACR Token Auth (Scope Map) Fix

Create a pull-only scope map for the three images:
```bash
SCOPE_MAP="pramana-pull-scope"

az acr scope-map create \
  --name "$SCOPE_MAP" \
  --registry "$ACR" \
  --repository pramana-gateway content/read \
  --repository pramana-verifier-text content/read \
  --repository pramana-verifier-media content/read
```

Create an ACR token bound to the scope map:
```bash
ACR_TOKEN="pramana-pull-token"

az acr token create \
  --name "$ACR_TOKEN" \
  --registry "$ACR" \
  --scope-map "$SCOPE_MAP"
```

Generate a token password (capture for registry auth):
```bash
ACR_TOKEN_PASSWORD=$(
  az acr token credential generate \
    --name "$ACR_TOKEN" \
    --registry "$ACR" \
    --password1 \
    --query passwords[0].value -o tsv
)
```

Update registry credentials for all three Container Apps using the token:
```bash
az containerapp registry set \
  --name pramana-gateway \
  --resource-group "$RG" \
  --server "$REGISTRY" \
  --username "$ACR_TOKEN" \
  --password "$ACR_TOKEN_PASSWORD"

az containerapp registry set \
  --name pramana-verifier-text \
  --resource-group "$RG" \
  --server "$REGISTRY" \
  --username "$ACR_TOKEN" \
  --password "$ACR_TOKEN_PASSWORD"

az containerapp registry set \
  --name pramana-verifier-media \
  --resource-group "$RG" \
  --server "$REGISTRY" \
  --username "$ACR_TOKEN" \
  --password "$ACR_TOKEN_PASSWORD"
```

Force new revisions by re-setting the images:
```bash
az containerapp update \
  --name pramana-gateway \
  --resource-group "$RG" \
  --image "$REGISTRY/pramana-gateway:$IMG_TAG"

az containerapp update \
  --name pramana-verifier-text \
  --resource-group "$RG" \
  --image "$REGISTRY/pramana-verifier-text:$IMG_TAG"

az containerapp update \
  --name pramana-verifier-media \
  --resource-group "$RG" \
  --image "$REGISTRY/pramana-verifier-media:$IMG_TAG"
```

Validation (gateway + system logs):
```bash
GATEWAY_FQDN=$(az containerapp show \
  -g "$RG" \
  -n pramana-gateway \
  --query properties.configuration.ingress.fqdn -o tsv)

curl "https://$GATEWAY_FQDN/node/metadata"

az containerapp logs show \
  --name pramana-gateway \
  --resource-group "$RG" \
  --type system
```

---

## STOP CHECKPOINT — STAGE B COMPLETE

Agent must stop and report:
- Resource names created
- Gateway URL
- Successful proof verification
- Approximate monthly cost estimate

---

## OPTIONAL CLEANUP (COST SAFETY)

```bash
az group delete --name "$RG" --yes --no-wait
```

---

## END OF DOCUMENT
