package com.example.truthlens

import android.os.Bundle
import android.text.method.LinkMovementMethod
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import com.example.truthlens.databinding.DialogVerifyResultBinding
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import org.json.JSONObject

class VerifyResultBottomSheet : BottomSheetDialogFragment() {

    private var _binding: DialogVerifyResultBinding? = null
    private val binding get() = _binding!!

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

        val jsonString = arguments?.getString(ARG_RESULT_JSON)
        if (jsonString != null) {
            displayResult(jsonString)
        } else {
            binding.resultText.text = "⚠️ No result data provided."
        }

        // Handle "Go to App" button
        binding.openAppButton.setOnClickListener {
            dismiss() // just close dialog for now, or navigate to VerifyActivity if needed
        }
    }

    private fun displayResult(result: String) {
        try {
            val json = JSONObject(result)
            val verdict = json.optString("verdict", "N/A").uppercase()
            val explanation = json.optString("explanation", "No explanation provided")
            val confidence = json.optDouble("confidence", 0.0)
            val citations = json.optJSONArray("citations")

            val factsText = buildString {
                append("✅ Verdict: $verdict\n")
                append("📊 Confidence: ${(confidence * 100).toInt()}%\n\n")
                append("📖 Explanation:\n$explanation\n\n")

                if (citations != null && citations.length() > 0) {
                    append("🔗 Citations:\n")
                    for (i in 0 until citations.length()) {
                        val c = citations.getJSONObject(i)
                        val title = c.optString("title", "Source")
                        val url = c.optString("url", "")
                        append("- $title ($url)\n")
                    }
                }
            }

            binding.resultText.text = factsText
            binding.statusText.text = "✅ Done"
        } catch (e: Exception) {
            binding.resultText.text = result
            binding.statusText.text = "⚠️ Parsing error"
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}