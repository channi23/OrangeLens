"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PramanaClient = void 0;
exports.computeContentHash = computeContentHash;
exports.attachProofToHeaders = attachProofToHeaders;
exports.attachProofToPostObject = attachProofToPostObject;
exports.attachProofToHTMLMeta = attachProofToHTMLMeta;
const crypto_1 = require("crypto");
function canonicalizeText(text) {
    return text.trim().replace(/\s+/g, " ");
}
function sha256Hex(value) {
    return (0, crypto_1.createHash)("sha256").update(value, "utf8").digest("hex");
}
function computeContentHash(input) {
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
function ensureFetch() {
    if (typeof fetch !== "function") {
        throw new Error("Fetch is not available. Use Node 18+ or provide a fetch polyfill.");
    }
    return fetch;
}
class PramanaClient {
    constructor(options) {
        this.baseUrl = options.baseUrl.replace(/\/$/, "");
    }
    async prepareVerify(request) {
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
    async verify(request) {
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
    async getRecordByHash(hash) {
        const doFetch = ensureFetch();
        const response = await doFetch(`${this.baseUrl}/truth_record/by_hash/${hash}`);
        if (!response.ok) {
            throw new Error(`getRecordByHash failed: ${response.status} ${await response.text()}`);
        }
        return response.json();
    }
}
exports.PramanaClient = PramanaClient;
function attachProofToHeaders(headers, proofResult) {
    return {
        ...headers,
        "X-Pramana-Proof": proofResult.proof,
    };
}
function attachProofToPostObject(post, proofResult) {
    return {
        ...post,
        pramana_proof: proofResult.proof,
    };
}
function attachProofToHTMLMeta(existingHtml, proofResult) {
    const metaTag = `<meta name=\"pramana-proof\" content=\"${proofResult.proof}\">`;
    if (/<head[^>]*>/i.test(existingHtml)) {
        return existingHtml.replace(/<head[^>]*>/i, (match) => `${match}\n  ${metaTag}`);
    }
    return `${existingHtml}\n${metaTag}`;
}
