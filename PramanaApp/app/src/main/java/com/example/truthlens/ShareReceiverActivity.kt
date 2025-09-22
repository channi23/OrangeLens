package com.example.truthlens

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.text.method.LinkMovementMethod
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.view.animation.AlphaAnimation
import android.view.animation.AnimationUtils
import androidx.appcompat.app.AppCompatActivity
import com.example.truthlens.databinding.DialogVerifyResultBinding
import com.google.android.material.bottomsheet.BottomSheetBehavior
import com.google.android.material.bottomsheet.BottomSheetDialog
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class ShareReceiverActivity : AppCompatActivity() {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    private val API_KEY = "AIzaSyDwfXPXq_ArGiVi7EAaT-fVTkOHUb_NXzA"
    private val BASE_URL = "https://truthlens-api-276376440888.us-central1.run.app/v1/verify"

    private lateinit var dialogBinding: DialogVerifyResultBinding
    private lateinit var bottomSheet: BottomSheetDialog

    private var sharedImageUri: Uri? = null
    private var lastRequestType: String? = null
    private var lastText: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        dialogBinding = DialogVerifyResultBinding.inflate(LayoutInflater.from(this))
        bottomSheet = BottomSheetDialog(this, R.style.TransparentBottomSheetDialog).apply {
            setContentView(dialogBinding.root)
            setCancelable(true)
        }

        // Ensure full-height bottom sheet
        bottomSheet.setOnShowListener { dialog ->
            val d = dialog as BottomSheetDialog
            d.findViewById<View>(com.google.android.material.R.id.design_bottom_sheet)?.let {
                val behavior = BottomSheetBehavior.from(it)
                behavior.state = BottomSheetBehavior.STATE_EXPANDED
                behavior.skipCollapsed = true
            }
        }

        // Finish activity only after sheet is dismissed (prevents background app freeze)
        bottomSheet.setOnDismissListener {
            finish()
        }

        bottomSheet.window?.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)

        // Enable links
        dialogBinding.resultText.movementMethod = LinkMovementMethod.getInstance()

        // Handle incoming shared intent
        handleSharedIntent(intent?.action, intent?.type)

        // Buttons
        dialogBinding.openAppButton.setOnClickListener {
            startActivity(Intent(this, VerifyActivity::class.java))
            bottomSheet.dismiss()
        }

        dialogBinding.closeButton.setOnClickListener {
            bottomSheet.dismiss()
        }

        dialogBinding.retryButton.setOnClickListener {
            when (lastRequestType) {
                "text" -> {
                    showLoading("⏳ Retrying text verification...")
                    sendTextToBackend(lastText)
                }
                "image" -> {
                    sharedImageUri?.let {
                        showLoading("⏳ Retrying image verification...")
                        sendImageToBackend(it)
                    } ?: run {
                        dialogBinding.resultText.text = "⚠️ No image available for retry"
                    }
                }
                else -> dialogBinding.resultText.text = "⚠️ Nothing to retry"
            }
        }

        bottomSheet.show()
    }

    private fun handleSharedIntent(action: String?, type: String?) {
        if (action == Intent.ACTION_SEND && type != null) {
            when {
                type.startsWith("text/") -> {
                    val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT)
                    if (!sharedText.isNullOrBlank()) {
                        lastRequestType = "text"
                        lastText = sharedText
                        showLoading("⏳ Sending text for verification...")
                        sendTextToBackend(sharedText)
                    } else {
                        showBottomSheet("{\"verdict\":\"N/A\",\"explanation\":\"Empty text\"}")
                    }
                }
                type.startsWith("image/") -> {
                    sharedImageUri = intent.getParcelableExtra(Intent.EXTRA_STREAM)
                    if (sharedImageUri != null) {
                        lastRequestType = "image"
                        lastText = ""
                        dialogBinding.resultImage.setImageURI(sharedImageUri)
                        dialogBinding.resultImage.visibility = View.VISIBLE
                        showLoading("⏳ Uploading image for verification...")
                        sendImageToBackend(sharedImageUri!!)
                    } else {
                        showBottomSheet("{\"verdict\":\"Error\",\"explanation\":\"No image received\"}")
                    }
                }
                else -> showBottomSheet("{\"verdict\":\"N/A\",\"explanation\":\"Unsupported content\"}")
            }
        } else {
            showBottomSheet("{\"verdict\":\"N/A\",\"explanation\":\"Nothing received\"}")
        }
    }

    // --- Loader controls ---
    private fun showLoading(status: String) {
        dialogBinding.loaderContainer.visibility = View.VISIBLE
        dialogBinding.loaderView.playAnimation()
        dialogBinding.loaderStatus.text = status

        dialogBinding.resultCard.visibility = View.GONE
        dialogBinding.verdictPill.visibility = View.GONE
        dialogBinding.retryButton.visibility = View.GONE
        dialogBinding.statusText.text = status
    }

    private fun hideLoading() {
        dialogBinding.loaderView.pauseAnimation()
        dialogBinding.loaderContainer.visibility = View.GONE
        dialogBinding.resultCard.visibility = View.VISIBLE

        // Animate result card
        val slideUp = AnimationUtils.loadAnimation(this, R.anim.slide_up)
        dialogBinding.resultCard.startAnimation(slideUp)
    }

    // --- Backend calls ---
    private fun sendTextToBackend(text: String) {
        val jsonBody = """{"text": "${text.replace("\"", "\\\"")}"}"""
            .toRequestBody("application/json; charset=utf-8".toMediaTypeOrNull())

        val request = Request.Builder()
            .url(BASE_URL)
            .addHeader("Content-Type", "application/json")
            .addHeader("Authorization", "Bearer $API_KEY")
            .post(jsonBody)
            .build()

        client.newCall(request).enqueue(makeCallback())
    }

    private fun sendImageToBackend(imageUri: Uri) {
        try {
            val imageBytes = contentResolver.openInputStream(imageUri)?.use { it.readBytes() }
            if (imageBytes == null) {
                runOnUiThread {
                    hideLoading()
                    showBottomSheet("{\"verdict\":\"Error\",\"explanation\":\"Could not read image\"}")
                }
                return
            }

            val requestBody = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("text", "")
                .addFormDataPart(
                    "image",
                    "shared.jpg",
                    imageBytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
                )
                .build()

            val request = Request.Builder()
                .url(BASE_URL)
                .addHeader("Authorization", "Bearer $API_KEY")
                .post(requestBody)
                .build()

            client.newCall(request).enqueue(makeCallback())
        } catch (e: Exception) {
            runOnUiThread {
                hideLoading()
                showBottomSheet("{\"verdict\":\"Error\",\"explanation\":\"${e.message}\"}")
            }
        }
    }

    // --- Callback handler ---
    private fun makeCallback(): Callback {
        return object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    hideLoading()
                    showBottomSheet("{\"verdict\":\"Error\",\"explanation\":\"${e.message}\"}")
                    dialogBinding.retryButton.visibility = View.VISIBLE
                }
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val result = if (response.isSuccessful) {
                        response.body?.string()
                            ?: "{\"verdict\":\"Unknown\",\"explanation\":\"Empty response\"}"
                    } else {
                        "{\"verdict\":\"Error\",\"explanation\":\"Error ${response.code}\"}"
                    }
                    runOnUiThread {
                        hideLoading()
                        showBottomSheet(result)
                        if (!response.isSuccessful) {
                            dialogBinding.retryButton.visibility = View.VISIBLE
                        }
                    }
                }
            }
        }
    }

    // --- Show results ---
    private fun showBottomSheet(resultJson: String) {
        dialogBinding.loaderContainer.visibility = View.GONE
        dialogBinding.loaderView.pauseAnimation()

        try {
            val json = JSONObject(resultJson)
            val verdict = json.optString("verdict", "N/A")
            val explanation = json.optString("explanation", "No explanation")
            val confidence = json.optDouble("confidence", 0.0)
            val citations = json.optJSONArray("citations")

            // Verdict pill
            val pill = dialogBinding.verdictPill
            pill.visibility = View.VISIBLE
            when (verdict.lowercase()) {
                "true" -> {
                    pill.text = "TRUE"
                    pill.setBackgroundResource(R.drawable.pill_true)
                }
                "false" -> {
                    pill.text = "FALSE"
                    pill.setBackgroundResource(R.drawable.pill_false)
                }
                "misleading" -> {
                    pill.text = "MISLEADING"
                    pill.setBackgroundResource(R.drawable.pill_misleading)
                }
                else -> {
                    pill.text = "UNKNOWN"
                    pill.setBackgroundResource(R.drawable.pill_unknown)
                }
            }
            val fadeIn = AlphaAnimation(0f, 1f).apply { duration = 400 }
            pill.startAnimation(fadeIn)

            // Build results
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

            dialogBinding.resultCard.visibility = View.VISIBLE
            dialogBinding.resultCard.startAnimation(
                AnimationUtils.loadAnimation(this, R.anim.slide_up)
            )
            dialogBinding.resultText.text = factsText

            dialogBinding.statusText.text = "✅ Done"
            dialogBinding.retryButton.visibility = View.GONE

        } catch (e: Exception) {
            dialogBinding.resultCard.visibility = View.VISIBLE
            dialogBinding.resultText.text = resultJson
            dialogBinding.statusText.text = "⚠️ Parsing error"
            dialogBinding.retryButton.visibility = View.VISIBLE
        }
    }
}