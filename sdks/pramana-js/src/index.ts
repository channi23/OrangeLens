import { createHash } from "crypto";

export type ContentType = "text" | "image" | "video" | "url";
export type Verdict = "true" | "misleading" | "unknown" | "unverified";
export type Confidence = "low" | "medium" | "high";

export interface Citation {
  title?: string | null;
  url?: string | null;
}

export interface VerificationRequest {
  content_type: ContentType;
  text?: string;
  source_url?: string;
  media_url?: string;
  content_hash?: string;
  client_id?: string;
}

export interface VerificationResult {
  record_id: string;
  content_hash: string;
  verdict: Verdict;
  truth_score: number;
  confidence: Confidence;
  explanation: string;
  citations: Citation[];
  issued_at: string;
  issuer: string;
  verdict_hash: string;
  proof: string;
  cached?: boolean;
}

export interface PramanaClientOptions {
  baseUrl: string;
}

function canonicalizeText(text: string): string {
  return text.trim().replace(/\s+/g, " ");
}

function sha256Hex(value: string): string {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

export function computeContentHash(input: VerificationRequest): string {
  if (input.content_hash) {
    return input.content_hash;
  }

  if (input.content_type === "text") {
    const normalized = canonicalizeText(input.text ?? "");
    if (!normalized) {
      throw new Error("Missing text for content_type=text");
    }
    return sha256Hex(normalized);
  }

  if (input.source_url) {
    return sha256Hex(String(input.source_url));
  }

  if (input.media_url) {
    return sha256Hex(String(input.media_url));
  }

  if (input.content_type === "image" || input.content_type === "video") {
    return "";
  }

  throw new Error("Missing content for hashing");
}

function ensureFetch(): typeof fetch {
  if (typeof fetch !== "function") {
    throw new Error("Fetch is not available. Use Node 18+ or provide a fetch polyfill.");
  }
  return fetch;
}

export class PramanaClient {
  private baseUrl: string;

  constructor(options: PramanaClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
  }

  async prepareVerify(request: VerificationRequest): Promise<{ content_hash: string }> {
    const doFetch = ensureFetch();
    const response = await doFetch(`${this.baseUrl}/prepare_verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      throw new Error(`prepare_verify failed: ${response.status} ${await response.text()}`);
    }
    return response.json();
  }

  async verify(request: VerificationRequest): Promise<VerificationResult> {
    const doFetch = ensureFetch();
    const response = await doFetch(`${this.baseUrl}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      throw new Error(`verify failed: ${response.status} ${await response.text()}`);
    }
    return response.json();
  }

  async getRecordByHash(hash: string): Promise<VerificationResult> {
    const doFetch = ensureFetch();
    const response = await doFetch(`${this.baseUrl}/truth_record/by_hash/${hash}`);
    if (!response.ok) {
      throw new Error(`getRecordByHash failed: ${response.status} ${await response.text()}`);
    }
    return response.json();
  }
}

export function attachProofToHeaders(
  headers: Record<string, string>,
  proofResult: VerificationResult
): Record<string, string> {
  return {
    ...headers,
    "X-Pramana-Proof": proofResult.proof,
  };
}

export function attachProofToPostObject<T extends Record<string, unknown>>(
  post: T,
  proofResult: VerificationResult
): T & { pramana_proof: string } {
  return {
    ...post,
    pramana_proof: proofResult.proof,
  };
}

export function attachProofToHTMLMeta(existingHtml: string, proofResult: VerificationResult): string {
  const metaTag = `<meta name=\"pramana-proof\" content=\"${proofResult.proof}\">`;
  if (/<head[^>]*>/i.test(existingHtml)) {
    return existingHtml.replace(/<head[^>]*>/i, (match) => `${match}\n  ${metaTag}`);
  }
  return `${existingHtml}\n${metaTag}`;
}
