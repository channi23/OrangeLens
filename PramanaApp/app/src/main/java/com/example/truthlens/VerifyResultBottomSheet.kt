package com.example.truthlens

import android.os.Bundle
import android.text.SpannableStringBuilder
import android.text.Spanned
import android.text.method.LinkMovementMethod
import android.text.style.URLSpan
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.ViewTreeObserver
import android.widget.Button
import com.google.android.material.button.MaterialButton
import android.widget.Toast
import androidx.lifecycle.lifecycleScope
import com.example.truthlens.core.parseVerifyResult
import com.example.truthlens.databinding.DialogVerifyResultBinding
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class VerifyResultBottomSheet : BottomSheetDialogFragment() {

    private var _binding: DialogVerifyResultBinding? = null
    private val binding get() = _binding!!
    private val scrollListener = ViewTreeObserver.OnScrollChangedListener {
        updateScrollIndicators()
    }

    companion object {
        private const val ARG_RESULT_JSON = "result_json"

        // Factory method → pass JSON string to fragment
        fun newInstance(resultJson: String): VerifyResultBottomSheet {
            val fragment = VerifyResultBottomSheet()
            val args = Bundle()
            args.putString(ARG_RESULT_JSON, resultJson)
            fragment.arguments = args
            return fragment
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = DialogVerifyResultBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.resultText.movementMethod = LinkMovementMethod.getInstance()
        setupScrollHandling()

        val jsonString = arguments?.getString(ARG_RESULT_JSON)
        if (jsonString != null) {
            displayResult(jsonString)
        } else {
            binding.resultText.text = "⚠️ No result data provided."
            binding.resultScroll.post { updateScrollIndicators() }
        }

        // Handle "Go to App" button
        binding.openAppButton.setOnClickListener {
            dismiss() // just close dialog for now, or navigate to VerifyActivity if needed
        }

    }

    private fun displayResult(result: String) {
        try {
            val uiState = parseVerifyResult(result)
            val verdict = uiState.verdict?.uppercase() ?: "N/A"
            val confidence = uiState.confidence
            val explanation = uiState.explanation ?: "No explanation provided"
            val citationsList = uiState.citationsDetailed
            val manipulationTechniqueRaw = uiState.manipulationTechnique?.trim().orEmpty()
            val manipulationExplanationRaw = uiState.manipulationExplanation?.trim().orEmpty()
            val timestamp = uiState.timestamp.orEmpty()
            val cached = uiState.cached == true
            val negativeVerdicts = setOf("FALSE", "MISLEADING", "SUSPICIOUS", "INCORRECT", "FAKE", "DECEPTIVE")
            val normalizedVerdict = uiState.verdict?.uppercase()
            val negativeVerdict = normalizedVerdict != null && normalizedVerdict in negativeVerdicts

            val sb = SpannableStringBuilder()
            var collapsedResult: CharSequence = ""

            sb.append("✅ Verdict: $verdict\n")
            sb.append("📊 Confidence: ${(confidence * 100).toInt()}%\n\n")

            sb.append("📖 Explanation:\n$explanation\n\n")

            if (negativeVerdict) {
                sb.append("──────────────────────────\n")
                sb.append("🎭 Manipulation Technique\n")
                sb.append("──────────────────────────\n")
                val techniqueText = when {
                    manipulationTechniqueRaw.isNotBlank() -> manipulationTechniqueRaw.replaceFirstChar { it.uppercase() }
                    negativeVerdict -> "Not provided"
                    else -> "Not detected"
                }
                val explanationText = when {
                    manipulationExplanationRaw.isNotBlank() -> manipulationExplanationRaw
                    negativeVerdict -> "No manipulation notes returned by the backend."
                    else -> "None provided"
                }
                sb.append("• Technique: $techniqueText\n")
                sb.append("• Explanation: $explanationText\n")
                if (!uiState.timestamp.isNullOrBlank()) {
                    sb.append("• Detected on: ${uiState.timestamp}\n")
                }
                sb.append("──────────────────────────\n\n")
            }

            val uniqueCitations = citationsList.distinctBy { it.second }
            if (uniqueCitations.isNotEmpty()) {
                val maxVisible = 3  // show first 3 citations before collapsing
                sb.append("🔗 Citations:\n")

                val displayCount = minOf(maxVisible, uniqueCitations.size)
                for (i in 0 until displayCount) {
                    val (rawTitle, rawUrl) = uniqueCitations[i]
                    val title = rawTitle.ifBlank { "Source ${i + 1}" }
                    val url = rawUrl
                    val start = sb.length
                    sb.append("• $title\n")
                    val end = sb.length
                    if (url.isNotBlank()) {
                        sb.setSpan(URLSpan(url), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                    }
                }

                // Handle overflow: show a "Show more sources…" link if more than 3 sources
                if (uniqueCitations.size > maxVisible) {
                    val start = sb.length
                    sb.append("Show more sources…")
                    val end = sb.length

                    sb.setSpan(object : URLSpan("#") {
                        override fun onClick(widget: View) {
                            val expanded = SpannableStringBuilder()
                            expanded.append("🔗 Citations:\n")
                            uniqueCitations.forEachIndexed { index, (rawTitle, rawUrl) ->
                                val title = rawTitle.ifBlank { "Source ${index + 1}" }
                                val url = rawUrl
                                val itemStart = expanded.length
                                expanded.append("• $title\n")
                                if (url.isNotBlank()) {
                                    val itemEnd = expanded.length
                                    expanded.setSpan(URLSpan(url), itemStart, itemEnd, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                                }
                            }
                            val showLessStart = expanded.length
                            expanded.append("Show less…")
                            val showLessEnd = expanded.length
                            expanded.setSpan(object : URLSpan("#") {
                                override fun onClick(widget: View) {
                                    binding.resultText.text = collapsedResult
                                    binding.resultText.movementMethod = LinkMovementMethod.getInstance()
                                    binding.resultScroll.post {
                                        binding.resultScroll.smoothScrollTo(0, 0)
                                        updateScrollIndicators()
                                    }
                                }
                            }, showLessStart, showLessEnd, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                            binding.resultText.text = expanded
                            binding.resultText.movementMethod = LinkMovementMethod.getInstance()
                            binding.resultScroll.post {
                                updateScrollIndicators()
                            }
                        }
                    }, start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                }

                sb.append("\n")
            } else {
                sb.append("🔗 Citations:\nNo citations provided.\n\n")
            }


            if (timestamp.isNotBlank()) {
                sb.append("⏰ Timestamp:\n$timestamp\n\n")
            }

            if (cached) {
                sb.append("🗂️ Cached result\n\n")
            }

            val finalText = sb.trim()
            collapsedResult = finalText
            binding.resultText.text = finalText
            binding.resultText.movementMethod = LinkMovementMethod.getInstance()
            binding.resultText.linksClickable = true

            // Add feedback buttons below the resultText dynamically
            binding.resultContainer.removeAllViews()
            binding.resultContainer.addView(binding.resultText)

            val helpfulButton = MaterialButton(requireContext()).apply {
                text = "👍 Accurate"
                setOnClickListener {
                    sendFeedback(uiState.requestId, "helpful")
                }
                setPadding(20, 10, 20, 10)
                setBackgroundColor(resources.getColor(R.color.teal_700, null))
                setTextColor(resources.getColor(android.R.color.white, null))
                cornerRadius = 20
            }
            val incorrectButton = MaterialButton(requireContext()).apply {
                text = "👎 Inaccurate"
                setOnClickListener {
                    sendFeedback(uiState.requestId, "incorrect")
                }
                setPadding(20, 10, 20, 10)
                setBackgroundColor(resources.getColor(android.R.color.holo_red_dark, null))
                setTextColor(resources.getColor(android.R.color.white, null))
                cornerRadius = 20
            }
            binding.resultContainer.addView(helpfulButton)
            binding.resultContainer.addView(incorrectButton)

            binding.statusText.text = "✅ Done"
            binding.resultScroll.post { updateScrollIndicators() }
        } catch (e: Exception) {
            binding.resultText.text = result
            binding.statusText.text = "⚠️ Parsing error"
            binding.resultScroll.post { updateScrollIndicators() }
        }
    }

    private fun sendFeedback(requestId: String?, feedbackType: String) {
        if (requestId.isNullOrBlank()) return
        lifecycleScope.launch(Dispatchers.IO) {
            try {
                val json = JSONObject().apply {
                    put("request_id", requestId)
                    put("feedback_type", feedbackType)
                }
                val url = URL("https://truthlens-api-276376440888.us-central1.run.app/v1/feedback")
                with(url.openConnection() as HttpURLConnection) {
                    requestMethod = "POST"
                    setRequestProperty("Content-Type", "application/json")
                    doOutput = true
                    outputStream.write(json.toString().toByteArray())
                    outputStream.flush()
                    if (responseCode == 200) {
                        withContext(Dispatchers.Main) {
                            Toast.makeText(requireContext(), "Feedback submitted!", Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    Toast.makeText(requireContext(), "Failed to send feedback.", Toast.LENGTH_SHORT).show()
                }
                android.util.Log.e("Feedback", "Error submitting feedback", e)
            }
        }
    }

    private fun setupScrollHandling() {
        binding.scrollIndicator.setOnClickListener {
            binding.resultScroll.smoothScrollBy(0, binding.resultScroll.height)
        }
        binding.resultScroll.viewTreeObserver.addOnScrollChangedListener(scrollListener)
    }

    private fun updateScrollIndicators() {
        val canScroll = binding.resultScroll.canScrollVertically(1)
        binding.scrollIndicator.visibility = if (canScroll) View.VISIBLE else View.GONE
        binding.scrollGradient.visibility = if (canScroll) View.VISIBLE else View.GONE
    }

    override fun onDestroyView() {
        binding.resultScroll.viewTreeObserver.removeOnScrollChangedListener(scrollListener)
        super.onDestroyView()
        _binding = null
    }
}
