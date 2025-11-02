package com.example.truthlens

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.example.truthlens.core.parseVerifyResult
import com.example.truthlens.ui.VerifyResultSheet
import com.example.truthlens.ui.theme.PramanaTheme
import com.example.truthlens.ui.theme.VerifyUiState
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
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
                var uiState by remember { mutableStateOf(VerifyUiState(status = "Idle")) }
                var showSheet by remember { mutableStateOf(true) }

                LaunchedEffect(action, type) {
                    if (action == Intent.ACTION_SEND && type != null) {
                        when {
                            type.startsWith("text/") -> {
                                val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT)
                                if (!sharedText.isNullOrBlank()) {
                                    lastRequestType = "text"
                                    lastText = sharedText
                                    uiState = uiState.copy(loading = true, status = "Sending text for verification...", showRetry = false)
                                    sendTextToBackend(sharedText) { result ->
                                        uiState = result
                                    }
                                } else {
                                    uiState = VerifyUiState(status = "Empty text", verdict = "N/A")
                                }
                            }
                            type.startsWith("image/") -> {
                                sharedImageUri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                                    intent.getParcelableExtra(Intent.EXTRA_STREAM, Uri::class.java)
                                } else {
                                    @Suppress("DEPRECATION")
                                    intent.getParcelableExtra(Intent.EXTRA_STREAM)
                                }

                                if (sharedImageUri != null) {
                                    lastRequestType = "image"
                                    lastText = ""
                                    uiState = VerifyUiState(loading = true, status = "Uploading image for verification...", imageUri = sharedImageUri)
                                    sendImageToBackend(sharedImageUri!!) { result ->
                                        uiState = result.copy(imageUri = sharedImageUri)
                                    }
                                } else {
                                    uiState = VerifyUiState(status = "No image received", verdict = "Error")
                                }
                            }
                            else -> uiState = VerifyUiState(status = "Unsupported content", verdict = "N/A")
                        }
                    } else {
                        uiState = VerifyUiState(status = "Nothing received", verdict = "N/A")
                    }
                }

                if (showSheet) {
                    VerifyResultSheet(
                        state = uiState,
                        sharedText = lastText,
                        sharedImageUri = sharedImageUri,
                        onContinue = {
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
                                    uiState = uiState.copy(loading = true, status = "Retrying text verification...", showRetry = false)
                                    sendTextToBackend(lastText) { res -> uiState = res }
                                }
                                "image" -> {
                                    sharedImageUri?.let { uri ->
                                        uiState = uiState.copy(loading = true, status = "Retrying image verification...", showRetry = false)
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
    private fun sendTextToBackend(text: String, onResult: (VerifyUiState) -> Unit) {
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

    private fun sendImageToBackend(imageUri: Uri, onResult: (VerifyUiState) -> Unit) {
        try {
            val imageBytes = contentResolver.openInputStream(imageUri)?.use { it.readBytes() }
            if (imageBytes == null) {
                runOnUiThread {
                    onResult(VerifyUiState(status = "Could not read image", verdict = "Error", showRetry = true))
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
                onResult(VerifyUiState(status = e.message ?: "Error", verdict = "Error", showRetry = true))
            }
        }
    }

    // --- Callback handler ---
    private fun makeCallback(onResult: (VerifyUiState) -> Unit): Callback {
        return object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    onResult(VerifyUiState(status = e.message ?: "Network error", verdict = "Error", showRetry = true))
                }
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val body = response.body?.string()
                    val ui = if (response.isSuccessful && body != null) parseResult(body)
                    else VerifyUiState(status = "Error ${response.code}", verdict = "Error", showRetry = true)
                    runOnUiThread { onResult(ui) }
                }
            }
        }
    }

    private fun parseResult(result: String): VerifyUiState = parseVerifyResult(result)
}
