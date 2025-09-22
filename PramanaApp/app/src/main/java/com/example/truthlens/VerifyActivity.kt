package com.example.truthlens

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.text.method.LinkMovementMethod
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import com.example.truthlens.databinding.ActivityVerifyBinding
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class VerifyActivity : AppCompatActivity() {
    private lateinit var binding: ActivityVerifyBinding

    // ✅ OkHttp client with extended timeouts
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    // ✅ Endpoints
    private val TEXT_ONLY_URL =
        "https://truthlens-api-276376440888.us-central1.run.app/v1/verify-test" // free
    private val COMBINED_URL =
        "https://truthlens-api-276376440888.us-central1.run.app/v1/verify" // requires API key

    // 🔑 API key (original key restored)
    private val API_KEY = "AIzaSyDwfXPXq_ArGiVi7EAaT-fVTkOHUb_NXzA"

    private val IMAGE_PICK_CODE = 1001
    private var selectedImageUri: Uri? = null

    // --- Retry tracking ---
    private var lastRequestType: String? = null  // "text" or "image"
    private var lastText: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityVerifyBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Make links clickable
        binding.verifyResult.movementMethod = LinkMovementMethod.getInstance()

        // Disable Verify button initially
        binding.verifyButton.isEnabled = false

        // Enable button when text or image is present
        binding.inputText.addTextChangedListener(object : TextWatcher {
            override fun afterTextChanged(s: Editable?) = toggleVerifyButton()
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
        })

        // Verify button → send text or text+image
        binding.verifyButton.setOnClickListener {
            val input = binding.inputText.text.toString().trim()
            if (input.isEmpty() && selectedImageUri == null) {
                binding.verifyResult.text = "⚠️ Please enter a claim or upload an image"
            } else {
                showLoader()
                if (selectedImageUri == null) {
                    lastRequestType = "text"
                    lastText = input
                    sendTextOnly(input)
                } else {
                    lastRequestType = "image"
                    lastText = input
                    sendTextAndImage(input, selectedImageUri!!)
                }
            }
        }

        // Retry button
        binding.retryButton.setOnClickListener {
            when (lastRequestType) {
                "text" -> {
                    showLoader()
                    sendTextOnly(lastText)
                }
                "image" -> {
                    if (selectedImageUri != null) {
                        showLoader()
                        sendTextAndImage(lastText, selectedImageUri!!)
                    } else {
                        binding.verifyResult.text = "⚠️ No image available for retry"
                    }
                }
                else -> binding.verifyResult.text = "⚠️ Nothing to retry"
            }
        }

        // Upload image
        binding.uploadImageButton.setOnClickListener { pickImageFromGallery() }

        // ✅ Handle quick-verify intent from MainActivity
        intent.getStringExtra("claim_text")?.let { quickClaim ->
            if (quickClaim.isNotEmpty()) {
                binding.inputText.setText(quickClaim)
                showLoader()
                lastRequestType = "text"
                lastText = quickClaim
                sendTextOnly(quickClaim)
            }
        }
    }

    // --- Enable/disable Verify button ---
    private fun toggleVerifyButton() {
        val hasText = binding.inputText.text.toString().trim().isNotEmpty()
        val hasImage = selectedImageUri != null
        binding.verifyButton.isEnabled = hasText || hasImage
    }

    // --- Loader controls ---
    private fun showLoader() {
        binding.loader.visibility = View.VISIBLE
        binding.loader.playAnimation()
        binding.verifyResult.text = ""
        binding.verdictCard.visibility = View.GONE
        binding.retryButton.visibility = View.GONE
    }

    private fun hideLoader() {
        binding.loader.pauseAnimation()
        binding.loader.visibility = View.GONE
    }

    // --- Pick image ---
    private fun pickImageFromGallery() {
        val intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.type = "image/*"
        startActivityForResult(Intent.createChooser(intent, "Select Image"), IMAGE_PICK_CODE)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == IMAGE_PICK_CODE && resultCode == Activity.RESULT_OK) {
            selectedImageUri = data?.data
            if (selectedImageUri != null) {
                binding.imagePreview.setImageURI(selectedImageUri)
                binding.imagePreview.visibility = View.VISIBLE
                toggleVerifyButton()
                binding.verifyResult.text = "✅ Image ready, now click Verify"
            }
        }
    }

    // --- Text-only (verify-test, no API key) ---
    private fun sendTextOnly(text: String) {
        val jsonMediaType = "application/json; charset=utf-8".toMediaTypeOrNull()
        val safeText = text.replace("\"", "\\\"")
        val jsonBody = """
            {"text": "$safeText", "mode": "fast", "language": "en"}
        """.trimIndent().toRequestBody(jsonMediaType)

        val request = Request.Builder()
            .url(TEXT_ONLY_URL)
            .addHeader("Content-Type", "application/json")
            .post(jsonBody)
            .build()

        client.newCall(request).enqueue(makeCallback())
    }

    // --- Text + Image (verify, API key required) ---
    private fun sendTextAndImage(text: String, imageUri: Uri) {
        try {
            val inputStream = contentResolver.openInputStream(imageUri)
            val imageBytes = inputStream?.readBytes()
            inputStream?.close()

            if (imageBytes == null) {
                runOnUiThread {
                    hideLoader()
                    binding.verifyResult.text = "❌ Could not read image"
                    binding.retryButton.visibility = View.VISIBLE
                }
                return
            }

            val bodyBuilder = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("mode", "fast")
                .addFormDataPart("language", "en")

            if (text.isNotEmpty()) {
                bodyBuilder.addFormDataPart("text", text)
            }

            bodyBuilder.addFormDataPart(
                "image",
                "upload.jpg",
                imageBytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
            )

            val request = Request.Builder()
                .url(COMBINED_URL)
                .addHeader("Authorization", "Bearer $API_KEY")
                .post(bodyBuilder.build())
                .build()

            client.newCall(request).enqueue(makeCallback())
        } catch (e: Exception) {
            runOnUiThread {
                hideLoader()
                binding.verifyResult.text = "❌ Error: ${e.message}"
                binding.retryButton.visibility = View.VISIBLE
            }
        }
    }

    // --- Callback for both ---
    private fun makeCallback(): Callback {
        return object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    hideLoader()
                    binding.verifyResult.text = "❌ Network error: ${e.message}"
                    binding.retryButton.visibility = View.VISIBLE
                }
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val bodyString = response.body?.string()
                    runOnUiThread {
                        hideLoader()
                        if (response.isSuccessful && bodyString != null) {
                            displayResult(bodyString)
                        } else {
                            binding.verifyResult.text =
                                "❌ Error ${response.code}: ${bodyString ?: "No response"}"
                            binding.retryButton.visibility = View.VISIBLE
                        }
                    }
                }
            }
        }
    }

    // --- Display verdict card + explanation ---
    private fun displayResult(result: String) {
        try {
            val json = JSONObject(result)
            val verdict = json.optString("verdict", "N/A").uppercase()
            val explanation = json.optString("explanation", "No explanation provided")
            val confidence = json.optDouble("confidence", 0.0)
            val citations = json.optJSONArray("citations")

            // Show verdict card
            binding.verdictCard.visibility = View.VISIBLE
            binding.verdictText.text = "Verdict: $verdict"
            binding.confidenceBar.progress = (confidence * 100).toInt()

            // Change card color based on verdict
            val color = when (verdict.lowercase()) {
                "true" -> resources.getColor(android.R.color.holo_green_dark, theme)
                "false" -> resources.getColor(android.R.color.holo_red_dark, theme)
                "misleading" -> resources.getColor(android.R.color.holo_orange_dark, theme)
                else -> resources.getColor(android.R.color.darker_gray, theme)
            }
            binding.verdictCard.setCardBackgroundColor(color)

            // Show explanation + citations
            val factsText = buildString {
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
            binding.verifyResult.text = factsText
            binding.retryButton.visibility = View.GONE

        } catch (e: Exception) {
            binding.verifyResult.text = "⚠️ Failed to parse response:\n$result"
            binding.retryButton.visibility = View.VISIBLE
        }
    }
}