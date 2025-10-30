// File: app/src/main/java/com/example/truthlens/ui/theme/VerifyUiState.kt
package com.example.truthlens.ui.theme

import android.net.Uri

data class VerifyUiState(
    val loading: Boolean = false,
    val status: String = "Idle",
    val verdict: String? = null,
    val explanation: String? = "",
    val confidence: Double = 0.0,
    val citations: List<Pair<String, String>> = emptyList(),
    val sources: List<String> = emptyList(),
    val showRetry: Boolean = false,
    val imageUri: Uri? = null,

    // Link scanning fields
    val linksFound: Int = 0,
    val unsafeLinks: List<LinkScanResult> = emptyList(),
    val hasUnsafeLinks: Boolean = false,
    val linkWarnings: List<String> = emptyList(),

    // NEW: Video & Feedback support
    val requestId: String? = null,
    val isVideoVerification: Boolean = false,
    val deepfakeDetected: Boolean = false,
    val deepfakeConfidence: Double = 0.0
)

data class LinkScanResult(
    val url: String,
    val isSafe: Boolean,
    val threatTypes: List<String>,
    val riskFactors: List<String>,
    val metadata: LinkMetadata?
)

data class LinkMetadata(
    val title: String?,
    val isHttps: Boolean,
    val hasRedirects: Boolean
)
