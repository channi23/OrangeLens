package com.example.truthlens.ui

import android.content.Context
import android.net.Uri
import android.os.Handler
import android.os.Looper
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.Crossfade
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.airbnb.lottie.compose.*
import com.example.truthlens.R
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit

// ✅ Backend details
private const val API_KEY = "AIzaSyDwfXPXq_ArGiVi7EAaT-fVTkOHUb_NXzA"
private const val BASE_URL = "https://truthlens-api-276376440888.us-central1.run.app/v1/verify"

@Composable
fun VerifyScreen(initialText: String? = null) {
    val context = LocalContext.current

    var input by remember { mutableStateOf(initialText ?: "") }
    var state by remember { mutableStateOf(VerifyUI(status = "Idle")) }
    var selectedImageUri by remember { mutableStateOf<Uri?>(null) }

    val client = remember {
        OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }
    val mainHandler = remember { Handler(Looper.getMainLooper()) }

    // Pick image
    val pickImageLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent(),
        onResult = { uri -> if (uri != null) selectedImageUri = uri }
    )

    // --- Network helpers ---
    fun postAndRender(request: Request, fallback: (() -> Unit)? = null) {
        state = state.copy(loading = true, status = "⏳ Verifying...", showRetry = false)
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                mainHandler.post {
                    state = VerifyUI(
                        status = "Network error: ${e.message}",
                        verdict = "Error",
                        showRetry = true
                    )
                }
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val bodyStr = response.body?.string()
                    if (response.isSuccessful && bodyStr != null) {
                        val ui = parseResult(bodyStr)
                        mainHandler.post { state = ui }
                    } else if (fallback != null) {
                        fallback()
                    } else {
                        mainHandler.post {
                            state = VerifyUI(
                                status = "HTTP ${response.code}: ${bodyStr ?: "No body"}",
                                verdict = "Error",
                                showRetry = true
                            )
                        }
                    }
                }
            }
        })
    }

    fun sendTextOnly(text: String) {
        val json = JSONObject().put("text", text).toString()
        val jsonBody = json.toRequestBody("application/json; charset=utf-8".toMediaType())
        val jsonReq = Request.Builder()
            .url(BASE_URL)
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer $API_KEY")
            .post(jsonBody)
            .build()

        // fallback as multipart
        val fallback = {
            val mp = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("text", text)
                .build()
            val mpReq = Request.Builder()
                .url(BASE_URL)
                .header("Authorization", "Bearer $API_KEY")
                .post(mp)
                .build()
            postAndRender(mpReq, fallback = null)
        }

        postAndRender(jsonReq, fallback)
    }

    fun sendImage(uri: Uri, ctx: Context) {
        state = state.copy(loading = true, status = "⏳ Uploading image...", showRetry = false)

        val inputStream = ctx.contentResolver.openInputStream(uri)
        val tempFile = File.createTempFile("upload", ".jpg", ctx.cacheDir).apply {
            outputStream().use { out -> inputStream?.copyTo(out) }
        }

        val mp = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("text", "")
            .addFormDataPart(
                "image", "upload.jpg",
                tempFile.asRequestBody("image/jpeg".toMediaTypeOrNull())
            )
            .build()

        val req = Request.Builder()
            .url(BASE_URL)
            .header("Authorization", "Bearer $API_KEY")
            .post(mp)
            .build()

        postAndRender(req, fallback = null)
    }

    LaunchedEffect(initialText) {
        if (!initialText.isNullOrBlank()) sendTextOnly(initialText)
    }

    // --- UI ---
    Column(
        modifier = Modifier
            .padding(20.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Text("🔍 Verify a Claim", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(12.dp))

        OutlinedTextField(
            value = input,
            onValueChange = { input = it },
            modifier = Modifier.fillMaxWidth(),
            placeholder = { Text("Enter text to verify") },
            singleLine = false,
            maxLines = 5,
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
            keyboardActions = KeyboardActions(onDone = {
                val t = input.trim()
                if (t.isNotEmpty()) sendTextOnly(t)
            })
        )

        Spacer(Modifier.height(12.dp))

        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(
                onClick = { val t = input.trim(); if (t.isNotEmpty()) sendTextOnly(t) },
                enabled = input.trim().isNotEmpty(),
                modifier = Modifier.weight(1f)
            ) { Text("Verify Text") }

            Button(
                onClick = { pickImageLauncher.launch("image/*") },
                modifier = Modifier.weight(1f)
            ) { Text("Pick Image") }
        }

        Spacer(Modifier.height(16.dp))

        // ✅ Reset button (only after result)
        AnimatedVisibility(visible = !state.loading && !state.verdict.isNullOrBlank()) {
            Button(
                onClick = {
                    input = ""
                    selectedImageUri = null
                    state = VerifyUI(status = "Idle")
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary)
            ) { Text("🔄 New Verification") }
        }

        Spacer(Modifier.height(16.dp))

        // Image preview + verify
        AnimatedVisibility(visible = selectedImageUri != null) {
            Column {
                AsyncImage(
                    model = selectedImageUri,
                    contentDescription = "Selected image",
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(180.dp)
                )
                Spacer(Modifier.height(8.dp))
                Button(
                    onClick = { selectedImageUri?.let { sendImage(it, context) } },
                    modifier = Modifier.fillMaxWidth()
                ) { Text("Verify Image") }
            }
        }

        Spacer(Modifier.height(16.dp))

        // Verdict pill
        AnimatedVisibility(visible = !state.loading && !state.verdict.isNullOrBlank()) {
            VerdictPill(verdict = state.verdict ?: "UNKNOWN")
        }

        Spacer(Modifier.height(12.dp))

        // ✅ Loader with loader.json
        Crossfade(targetState = state.loading, label = "verify_loader") { isLoading ->
            if (isLoading) {
                LoaderBlock(status = state.status)
            } else {
                ResultCard(state = state)
            }
        }
    }
}

@Composable
private fun LoaderBlock(status: String) {
    val composition by rememberLottieComposition(LottieCompositionSpec.RawRes(R.raw.loader))
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .height(240.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // ✅ medium size loader
        LottieAnimation(
            composition = composition,
            iterations = LottieConstants.IterateForever,
            modifier = Modifier.size(180.dp)
        )
        Spacer(Modifier.height(16.dp))
        Text(status, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)
    }
}

// --- Parse backend JSON ---
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
        VerifyUI(
            loading = false,
            status = "⚠️ Parsing error: ${e.message}",
            verdict = "Unknown",
            showRetry = true
        )
    }
}