package com.example.truthlens.core

import android.util.Log
import com.example.truthlens.ui.theme.VerifyUiState
import org.json.JSONObject

fun parseVerifyResult(result: String): VerifyUiState {
    return try {
        val json = JSONObject(result)

        if (json.has("detail") && !json.has("verdict")) {
            return VerifyUiState(
                loading = false,
                status = "Verification Failed",
                explanation = json.optString("detail"),
                verdict = "Error",
                showRetry = true
            )
        }

        var verdict = json.optString("verdict", "N/A").uppercase()
        if (verdict == "UNVERIFIABLE" || verdict == "UNKNOWN") verdict = "UNVERIFIED"

        val explanationRaw = sanitizeExplanationForUser(
            json.optString("explanation")?.ifBlank { "No explanation provided" },
            json
        )
        val confidence = json.optDouble("confidence", 0.0)
        val requestId = json.optString("request_id", null)

        val deepfake = json.optJSONObject("deepfake") ?: JSONObject()
        val deepfakeDetected = deepfake.optBoolean("detected", false)
        val deepfakeConfidence = deepfake.optDouble("confidence", 0.0)

        val manipulation = json.optJSONObject("manipulation")
        var manipulationTechnique: String? = null
        var manipulationExplanation: String? = null
        if (manipulation != null) {
            manipulationTechnique = manipulation.optString("technique", null)
            manipulationExplanation = manipulation.optString("explanation", null)
        }
        if (manipulationTechnique.isNullOrBlank()) {
            manipulationTechnique = json.optString("manipulation_technique", null)
        }
        if (manipulationExplanation.isNullOrBlank()) {
            manipulationExplanation = json.optString("manipulation_explanation", null)
        }
        manipulationTechnique = manipulationTechnique ?: ""
        manipulationExplanation = manipulationExplanation ?: ""
        val hasManipulationData = manipulationTechnique.isNotBlank() || manipulationExplanation.isNotBlank()

        val timestamp = json.optString("timestamp", "")

        val keyFactsArray = json.optJSONArray("key_facts")
        val keyFacts = buildList {
            if (keyFactsArray != null) {
                for (i in 0 until keyFactsArray.length()) {
                    add(keyFactsArray.optString(i))
                }
            }
        }

        val factChecksArray = json.optJSONArray("fact_check_results")
        val factChecks = buildList {
            if (factChecksArray != null) {
                for (i in 0 until factChecksArray.length()) {
                    add(factChecksArray.optString(i))
                }
            }
        }

        val citationsDetailed = buildList {
            val primary = json.optJSONArray("citationsDetailed")
                ?: json.optJSONArray("citations")
                ?: json.optJSONArray("sources")
            if (primary != null) {
                for (i in 0 until primary.length()) {
                    val item = primary.opt(i)
                    when (item) {
                        is JSONObject -> {
                            val title = item.optString("title", "Source")
                            val url = item.optString("url", "")
                            add(title to url)
                        }
                        is String -> {
                            add("Source" to item)
                        }
                    }
                }
            }
        }

        val forensics = json.optJSONObject("media_forensics") ?: JSONObject()
        val frameCount = forensics.optJSONObject("probe")?.optInt("frame_count", -1)
        val explanationClean = explanationRaw.replace(
            Regex("\\(Analyzed.*?frames.*?\\)", RegexOption.IGNORE_CASE),
            ""
        ).trim()
        val forensicNote = if (frameCount != null && frameCount > 0)
            "(Analyzed $frameCount frames with fused forensic + LLM analysis.)"
        else ""
        val finalExplanation = listOf(explanationClean, forensicNote)
            .filter { it.isNotBlank() }
            .joinToString(" ")

        val cached = json.optBoolean("cached", false)

        Log.d(
            "VerifyResultParser",
            "Parsed verdict: $verdict, manipulationTechnique: \"$manipulationTechnique\", manipulationExplanation: \"$manipulationExplanation\", " +
                    "citationsDetailed: $citationsDetailed, hasManipulationData: $hasManipulationData, cached: $cached"
        )

        VerifyUiState(
            loading = false,
            status = "Done",
            verdict = verdict,
            explanation = finalExplanation,
            confidence = confidence,
            deepfakeDetected = deepfakeDetected,
            deepfakeConfidence = deepfakeConfidence,
            manipulationTechnique = manipulationTechnique,
            manipulationExplanation = manipulationExplanation,
            timestamp = timestamp,
            keyFacts = keyFacts,
            factChecks = factChecks,
            requestId = requestId,
            showRetry = false,
            cached = cached,
            citationsDetailed = citationsDetailed,
            hasManipulationData = hasManipulationData
        )
    } catch (ex: Exception) {
        Log.e("VerifyResultParser", "Error parsing result: ${ex.message}", ex)
        VerifyUiState(
            loading = false,
            status = "Parsing error",
            explanation = "Could not parse response: ${ex.message}",
            verdict = "Unknown",
            showRetry = true
        )
    }
}

private fun sanitizeExplanationForUser(raw: String?, json: JSONObject): String {
    val safeInput = try {
        raw?.trim()?.encodeToByteArray()?.toString(Charsets.UTF_8) ?: ""
    } catch (_: Exception) {
        raw ?: ""
    }
    val input = safeInput
    val insufficient = json.optBoolean("insufficient_frames", false) ||
            input.contains("not enough frame", ignoreCase = true) ||
            input.contains("insufficient frame", ignoreCase = true)

    val safe = if (insufficient) {
        "$input (Analysis limited due to few available frames.)"
    } else input

    val keyframes = json.optJSONArray("video_keyframes")?.length()
        ?: json.optInt("frame_count", -1)
    return if (keyframes > 0) {
        val prefix = if (safe.isBlank()) "" else "$safe "
        "$prefix(Analyzed $keyframes keyframes with fused forensic + LLM signals.)"
    } else {
        safe
    }
}
