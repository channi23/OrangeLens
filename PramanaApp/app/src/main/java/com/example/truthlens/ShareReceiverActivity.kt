package com.example.truthlens

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.*
import com.example.truthlens.ui.VerifyResultSheet
import com.example.truthlens.ui.VerifyUI
import com.example.truthlens.ui.theme.PramanaTheme
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class ShareReceiverActivity : ComponentActivity() {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    private val API_KEY = "AIzaSyDwfXPXq_ArGiVi7EAaT-fVTkOHUb_NXzA"
    private val BASE_URL = "https://truthlens-api-276376440888.us-central1.run.app/v1/verify"

    private var sharedImageUri: Uri? = null
    private var lastRequestType: String? = null
    private var lastText: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val action = intent?.action
        val type = intent?.type

        setContent {
            PramanaTheme {
                var uiState by remember { mutableStateOf(VerifyUI(status = "Idle")) }
                var showSheet by remember { mutableStateOf(true) }

                LaunchedEffect(action, type) {
                    if (action == Intent.ACTION_SEND && type != null) {
                        when {
                            type.startsWith("text/") -> {
                                val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT)
                                if (!sharedText.isNullOrBlank()) {
                                    lastRequestType = "text"
                                    lastText = sharedText
                                    uiState = uiState.copy(loading = true, status = "⏳ Sending text for verification...", showRetry = false)
                                    sendTextToBackend(sharedText) { result ->
                                        uiState = result
                                    }
                                } else {
                                    uiState = VerifyUI(status = "Empty text", verdict = "N/A")
                                }
                            }
                            type.startsWith("image/") -> {
                                sharedImageUri = intent.getParcelableExtra(Intent.EXTRA_STREAM)
                                if (sharedImageUri != null) {
                                    lastRequestType = "image"
                                    lastText = ""
                                    uiState = VerifyUI(loading = true, status = "⏳ Uploading image for verification...", imageUri = sharedImageUri)
                                    sendImageToBackend(sharedImageUri!!) { result ->
                                        uiState = result.copy(imageUri = sharedImageUri)
                                    }
                                } else {
                                    uiState = VerifyUI(status = "No image received", verdict = "Error")
                                }
                            }
                            else -> uiState = VerifyUI(status = "Unsupported content", verdict = "N/A")
                        }
                    } else {
                        uiState = VerifyUI(status = "Nothing received", verdict = "N/A")
                    }
                }

                if (showSheet) {
                    VerifyResultSheet(
                        state = uiState,
                        onContinue = {
                            startActivity(Intent(this, VerifyActivity::class.java))
                            showSheet = false
                            finish()
                        },
                        onClose = {
                            showSheet = false
                            finish()
                        },
                        onRetry = {
                            when (lastRequestType) {
                                "text" -> {
                                    uiState = uiState.copy(loading = true, status = "⏳ Retrying text verification...", showRetry = false)
                                    sendTextToBackend(lastText) { res -> uiState = res }
                                }
                                "image" -> {
                                    sharedImageUri?.let { uri ->
                                        uiState = uiState.copy(loading = true, status = "⏳ Retrying image verification...", showRetry = false)
                                        sendImageToBackend(uri) { res -> uiState = res.copy(imageUri = uri) }
                                    }
                                }
                                else -> { /* nothing */ }
                            }
                        },
                        onDismissRequest = {
                            showSheet = false
                            finish()
                        }
                    )
                }
            }
        }
    }

    // --- Backend calls ---
    private fun sendTextToBackend(text: String, onResult: (VerifyUI) -> Unit) {
        val jsonBody = """{"text": "${text.replace("\"", "\\\"")}"}"""
            .toRequestBody("application/json; charset=utf-8".toMediaTypeOrNull())

        val request = Request.Builder()
            .url(BASE_URL)
            .addHeader("Content-Type", "application/json")
            .addHeader("Authorization", "Bearer $API_KEY")
            .post(jsonBody)
            .build()

        client.newCall(request).enqueue(makeCallback(onResult))
    }

    private fun sendImageToBackend(imageUri: Uri, onResult: (VerifyUI) -> Unit) {
        try {
            val imageBytes = contentResolver.openInputStream(imageUri)?.use { it.readBytes() }
            if (imageBytes == null) {
                runOnUiThread {
                    onResult(VerifyUI(status = "Could not read image", verdict = "Error", showRetry = true))
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

            client.newCall(request).enqueue(makeCallback(onResult))
        } catch (e: Exception) {
            runOnUiThread {
                onResult(VerifyUI(status = e.message ?: "Error", verdict = "Error", showRetry = true))
            }
        }
    }

    // --- Callback handler ---
    private fun makeCallback(onResult: (VerifyUI) -> Unit): Callback {
        return object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    onResult(VerifyUI(status = e.message ?: "Network error", verdict = "Error", showRetry = true))
                }
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val body = response.body?.string()
                    val ui = if (response.isSuccessful && body != null) parseResult(body)
                    else VerifyUI(status = "Error ${response.code}", verdict = "Error", showRetry = true)
                    runOnUiThread { onResult(ui) }
                }
            }
        }
    }

    private fun parseResult(result: String): VerifyUI {
        return try {
            val json = JSONObject(result)
            val verdict = json.optString("verdict", "N/A").uppercase()
            val explanation = json.optString("explanation", "No explanation provided")
            val confidence = json.optDouble("confidence", 0.0)
            val citationsArr = json.optJSONArray("citations")
            val citations = buildList {
                if (citationsArr != null) {
                    for (i in 0 until citationsArr.length()) {
                        val c = citationsArr.getJSONObject(i)
                        add(c.optString("title", "Source") to c.optString("url", ""))
                    }
                }
            }
            VerifyUI(
                loading = false,
                status = "✅ Done",
                verdict = verdict,
                explanation = explanation,
                confidence = confidence,
                citations = citations,
                showRetry = false
            )
        } catch (e: Exception) {
            VerifyUI(loading = false, status = "⚠️ Parsing error", verdict = "Unknown", showRetry = true)
        }
    }
}
