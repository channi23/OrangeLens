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
export declare function computeContentHash(input: VerificationRequest): string;
export declare class PramanaClient {
    private baseUrl;
    constructor(options: PramanaClientOptions);
    prepareVerify(request: VerificationRequest): Promise<{
        content_hash: string;
    }>;
    verify(request: VerificationRequest): Promise<VerificationResult>;
    getRecordByHash(hash: string): Promise<VerificationResult>;
}
export declare function attachProofToHeaders(headers: Record<string, string>, proofResult: VerificationResult): Record<string, string>;
export declare function attachProofToPostObject<T extends Record<string, unknown>>(post: T, proofResult: VerificationResult): T & {
    pramana_proof: string;
};
export declare function attachProofToHTMLMeta(existingHtml: string, proofResult: VerificationResult): string;
