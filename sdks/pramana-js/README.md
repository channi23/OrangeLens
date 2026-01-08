# Pramana JS SDK (MVP)

Minimal TypeScript-first SDK for integrating with the Pramana gateway.

## Install (local)

```bash
cd sdks/pramana-js
npm install
npm run build
npm link
```

In another project:

```bash
npm link pramana-js
```

## Usage

```ts
import { PramanaClient, attachProofToPostObject } from "pramana-js";

const client = new PramanaClient({ baseUrl: "http://localhost:8000" });

const result = await client.verify({
  content_type: "text",
  text: "Breaking: scientists discover water on Mars again",
});

const postPayload = attachProofToPostObject(
  { text: "Hello world" },
  result
);

console.log(result.cached, result.proof);
console.log(postPayload);
```

## Proof helpers

- `attachProofToHeaders(headers, result)`
- `attachProofToPostObject(post, result)`
- `attachProofToHTMLMeta(html, result)`

## Example (quickstart)

```bash
cd sdks/pramana-js
npm install
npm run build
node dist/examples/quickstart.js
```

Set a custom gateway URL:

```bash
PRAMANA_BASE_URL=http://localhost:8000 node dist/examples/quickstart.js
```
