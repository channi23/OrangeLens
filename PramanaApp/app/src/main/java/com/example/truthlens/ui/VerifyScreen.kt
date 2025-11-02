// File: app/src/main/java/com/example/truthlens/ui/VerifyScreen.kt
package com.example.truthlens.ui

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.rounded.CameraAlt
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material.icons.rounded.Image
import androidx.compose.material.icons.rounded.Menu
import androidx.compose.material.icons.rounded.OpenInNew
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material.icons.rounded.ThumbDown
import androidx.compose.material.icons.rounded.ThumbUp
import androidx.compose.material.icons.rounded.TrendingUp
import androidx.compose.material.icons.rounded.Videocam
import androidx.compose.material.icons.rounded.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.zIndex
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import coil.compose.AsyncImage
import com.example.truthlens.R
import com.example.truthlens.core.parseVerifyResult
import com.example.truthlens.ui.theme.VerifyUiState
import kotlinx.coroutines.delay
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.concurrent.TimeUnit

// API Endpoints
private const val API_KEY = "AIzaSyDwfXPXq_ArGiVi7EAaT-fVTkOHUb_NXzA" // Replace with your actual API key
private const val BASE_URL = "https://truthlens-api-276376440888.us-central1.run.app/v1"
private const val VERIFY_URL = "$BASE_URL/verify"
private const val VERIFY_MEDIA_URL = "$BASE_URL/verify_media"
private const val FEEDBACK_URL = "$BASE_URL/feedback"
private const val TRENDING_URL = "$BASE_URL/trending"

// Attach both headers; backend may accept either Authorization: Bearer or x-api-key
private fun Request.Builder.withAuth(): Request.Builder {
    return this
        .header("Authorization", "Bearer $API_KEY")
        .header("x-api-key", API_KEY)
}

// Theming
private val LightBackground = Color(0xFFFAFAFA)
private val LightForeground = Color(0xFF1E1E1E)
private val LightCard = Color(0xFFFFFFFF)
private val LightBorder = Color(0xFFE5E7EB)
private val LightMuted = Color(0xFF6B7280)
private val DarkBackground = Color(0xFF0F0F0F)
private val DarkForeground = Color(0xFFE5E5E5)
private val DarkCard = Color(0xFF1A1A1A)
private val DarkBorder = Color(0xFF2A2A2A)
private val DarkMuted = Color(0xFF9CA3AF)
private val PrimaryDark = Color(0xFF1E293B)
private val SuccessGreen = Color(0xFF10B981)
private val ErrorRed = Color(0xFFEF4444)
private val WarningYellow = Color(0xFFF59E0B)

data class ThemeColors(
    val background: Color,
    val foreground: Color,
    val card: Color,
    val border: Color,
    val muted: Color,
    val buttonPrimary: Color = PrimaryDark,
    val buttonSecondary: Color = Color.White
)

fun getLightTheme() = ThemeColors(
    background = LightBackground,
    foreground = LightForeground,
    card = LightCard,
    border = LightBorder,
    muted = LightMuted
)

fun getDarkTheme() = ThemeColors(
    background = DarkBackground,
    foreground = DarkForeground,
    card = DarkCard,
    border = DarkBorder,
    muted = DarkMuted
)

// Data Classes
data class SearchHistoryItem(
    val id: String = System.currentTimeMillis().toString(),
    val text: String,
    val timestamp: Long = System.currentTimeMillis(),
    val mediaUri: Uri? = null,
    val verdict: String? = null,
    val explanation: String? = null,
    val confidence: Double = 0.0,
    val citationsDetailed: List<Pair<String, String>> = emptyList(),
    val requestId: String? = null,
    val isVideoVerification: Boolean = false,
    val deepfakeDetected: Boolean = false,
    val deepfakeConfidence: Double = 0.0
)

data class TrendingItem(
    val text: String,
    val count: Int,
    val lastSeen: String
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VerifyScreen(
    initialText: String? = null,
    initialImageUri: Uri? = null
) {
    val context = LocalContext.current
    var input by remember { mutableStateOf(initialText ?: "") }
    var state by remember { mutableStateOf(VerifyUiState()) }
    var selectedMediaUri by remember { mutableStateOf<Uri?>(initialImageUri) }
    var selectedMediaType by remember { mutableStateOf<String?>(if (initialImageUri != null) "image" else null) }

    var sidebarOpen by remember { mutableStateOf(false) }
    var searchHistory by remember { mutableStateOf<List<SearchHistoryItem>>(emptyList()) }
    var isDarkMode by remember { mutableStateOf(false) }

    var showTrending by remember { mutableStateOf(false) }
    var trendingItems by remember { mutableStateOf<List<TrendingItem>>(emptyList()) }
    var loadingTrending by remember { mutableStateOf(false) }

    val colors = if (isDarkMode) getDarkTheme() else getLightTheme()

    val client = remember {
        OkHttpClient.Builder()
            .connectTimeout(120, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)
            .writeTimeout(120, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()
    }
    val mainHandler = remember { Handler(Looper.getMainLooper()) }

    val cameraImageUri = remember { mutableStateOf<Uri?>(null) }

    fun createImageFile(ctx: Context): Uri {
        val storageDir = ctx.getExternalFilesDir(Environment.DIRECTORY_PICTURES)
        storageDir?.mkdirs()
        val timeStamp = System.currentTimeMillis()
        the@ run { }
        val imageFile = File(storageDir, "IMG_${timeStamp}.jpg")
        return FileProvider.getUriForFile(ctx, "${ctx.packageName}.provider", imageFile)
    }

    // --- Unified media picker (unchanged) ---
    val pickMediaLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri ->
        if (uri != null) {
            val mimeType = context.contentResolver.getType(uri)
            selectedMediaUri = uri
            selectedMediaType = when {
                mimeType?.startsWith("video/") == true -> "video"
                mimeType?.startsWith("image/") == true -> "image"
                else -> null
            }
        }
    }

    val takePictureLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture()
    ) { success ->
        if (success && cameraImageUri.value != null) {
            selectedMediaUri = cameraImageUri.value
            selectedMediaType = "image"
        }
    }

    val cameraPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            try {
                val uri = createImageFile(context)
                cameraImageUri.value = uri
                takePictureLauncher.launch(uri)
            } catch (ex: Exception) {
                android.util.Log.e("Camera", "Error creating file: ${ex.message}", ex)
            }
        }
    }

    fun addToHistory(text: String, uri: Uri?, verifyState: VerifyUiState) {
        if (text.trim().isNotEmpty() || uri != null) {
            // Use citationsDetailed if available and non-empty, else store emptyList
            val citationsToStore = verifyState.citationsDetailed.takeIf { it.isNotEmpty() } ?: emptyList()
            searchHistory = listOf(
                SearchHistoryItem(
                    text = text,
                    mediaUri = uri,
                    verdict = verifyState.verdict,
                    explanation = verifyState.explanation,
                    confidence = verifyState.confidence,
                    citationsDetailed = citationsToStore,
                    requestId = verifyState.requestId,
                    isVideoVerification = verifyState.isVideoVerification,
                    deepfakeDetected = verifyState.deepfakeDetected,
                    deepfakeConfidence = verifyState.deepfakeConfidence
                )
            ) + searchHistory.take(24)
        }
    }

    fun fetchTrendingItems() {
        loadingTrending = true
        val request = Request.Builder()
            .withAuth()
            .url(TRENDING_URL)
            .get()
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, ex: IOException) {
                mainHandler.post { loadingTrending = false }
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val bodyStr = it.body?.string()
                    if (it.isSuccessful && bodyStr != null) {
                        try {
                            val json = JSONObject(bodyStr)
                            val trendingArray = json.optJSONArray("trending")
                            val items = mutableListOf<TrendingItem>()
                            if (trendingArray != null) {
                                for (i in 0 until trendingArray.length()) {
                                    val item = trendingArray.getJSONObject(i)
                                    items.add(
                                        TrendingItem(
                                            text = item.optString("text", ""),
                                            count = item.optInt("count", 0),
                                            lastSeen = item.optString("last_seen", "")
                                        )
                                    )
                                }
                            }
                            mainHandler.post {
                                trendingItems = items
                                showTrending = true
                                loadingTrending = false
                            }
                        } catch (ex: Exception) {
                            mainHandler.post { loadingTrending = false }
                        }
                    } else {
                        mainHandler.post { loadingTrending = false }
                    }
                }
            }
        })
    }

    fun postAndRender(request: Request, originalText: String, isVideoVerification: Boolean? = null) {
        state = state.copy(loading = true, status = "Verifying...", verdict = null, showRetry = false)
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, ex: IOException) {
                mainHandler.post {
                    val errorState = VerifyUiState(
                        loading = false,
                        status = "Verification Failed",
                        explanation = "Network Error: ${ex.message}",
                        verdict = "Error",
                        showRetry = true
                    )
                    state = errorState
                    addToHistory(originalText, selectedMediaUri, errorState)
                }
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val bodyStr = it.body?.string()
                    val maybeJson = try { if (bodyStr != null) JSONObject(bodyStr) else null } catch (_: Exception) { null }
                    val ui = if (it.isSuccessful && bodyStr != null) {
                        parseVerifyResult(bodyStr).copy(imageUri = selectedMediaUri)
                    } else {
                        VerifyUiState(
                            loading = false,
                            status = "Verification Failed",
                            explanation = buildString {
                                append("Server Error ${it.code}")
                                val detail = maybeJson?.optString("detail")?.takeIf { d -> d.isNotBlank() }
                                    ?: maybeJson?.optString("message")?.takeIf { d -> d.isNotBlank() }
                                if (detail != null) append(": $detail")
                                else if (!bodyStr.isNullOrBlank()) append(": $bodyStr")
                            },
                            verdict = "Error",
                            showRetry = true
                        )
                    }
                    val finalUi = if (isVideoVerification != null) ui.copy(isVideoVerification = isVideoVerification) else ui
                    android.util.Log.e(
                        "VerifyRequest",
                        "HTTP ${response.code} ${response.message} | isVideo=$isVideoVerification | body=${bodyStr?.take(1000)}"
                    )
                    android.util.Log.e("VerifyResponse", "Full response body: ${bodyStr?.take(3000)}")
                    addToHistory(originalText, selectedMediaUri, finalUi)
                    mainHandler.post { state = finalUi }
                }
            }
        })
    }

    fun sendFeedback(requestId: String, feedbackType: String) {
        val jsonBody = JSONObject().apply {
            put("request_id", requestId)
            put("feedback", feedbackType)
            // Add fallback comment field for backend
            put("comment", "User feedback from app")
        }.toString()

        val requestBody = jsonBody.toRequestBody("application/json".toMediaTypeOrNull())

        val request = Request.Builder()
            .withAuth()
            .url(FEEDBACK_URL)
            .post(requestBody)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                android.util.Log.e("Feedback", "Feedback failed to send: ${e.message}", e)
                mainHandler.post { Toast.makeText(context, "Feedback failed to send.", Toast.LENGTH_SHORT).show() }
            }

            override fun onResponse(call: Call, response: Response) {
                try {
                    mainHandler.post {
                        if (response.isSuccessful) {
                            Toast.makeText(context, "Thank you for your feedback!", Toast.LENGTH_SHORT).show()
                        } else {
                            android.util.Log.e("Feedback", "Feedback API error: ${response.code} - ${response.message}")
                        }
                    }
                } finally {
                    response.close()
                }
            }
        })
    }

    fun getSupportedLanguage(ctx: Context): String {
        val localeLang = Locale.getDefault().language
        return when (localeLang.lowercase()) {
            "en", "hi", "ta", "te" -> localeLang.lowercase()
            else -> "en"
        }
    }

    fun sendTextOnly(text: String) {
        val jsonBody = JSONObject().apply {
            put("text", text)
            put("language", getSupportedLanguage(context))
            put("mode", "fast")
        }.toString().toRequestBody("application/json".toMediaTypeOrNull())

        val jsonReq = Request.Builder()
            .withAuth()
            .url(VERIFY_URL)
            .post(jsonBody)
            .build()

        state = state.copy(loading = true, status = "Verifying...", verdict = null, showRetry = false)

        client.newCall(jsonReq).enqueue(object : Callback {
            override fun onFailure(call: Call, ex: IOException) {
                val errorState = VerifyUiState(
                    loading = false,
                    status = "Verification Failed",
                    explanation = "Network Error: ${ex.message}",
                    verdict = "Error",
                    showRetry = true
                )
                mainHandler.post { state = errorState }
                addToHistory(text, null, errorState)
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val bodyStr = it.body?.string()
                    if (it.isSuccessful && bodyStr != null) {
                        val ui = parseVerifyResult(bodyStr)
                        addToHistory(text, null, ui)
                        mainHandler.post { state = ui }
                    } else {
                        // 🔄 fallback for form-data (in case backend expects multipart)
                        val mp = MultipartBody.Builder()
                            .setType(MultipartBody.FORM)
                            .addFormDataPart("text", text)
                            .addFormDataPart("language", getSupportedLanguage(context))
                            .addFormDataPart("mode", "fast")
                            .build()
                        val formReq = Request.Builder()
                            .withAuth()
                            .url(VERIFY_URL)
                            .post(mp)
                            .build()
                        client.newCall(formReq).enqueue(object : Callback {
                            override fun onFailure(call2: Call, ex2: IOException) {
                                val errorState = VerifyUiState(
                                    loading = false,
                                    status = "Verification Failed",
                                    explanation = "Network Error: ${ex2.message}",
                                    verdict = "Error",
                                    showRetry = true
                                )
                                mainHandler.post { state = errorState }
                            }

                            override fun onResponse(call2: Call, response2: Response) {
                                response2.use {
                                    val bodyStr2 = it.body?.string()
                                    if (it.isSuccessful && bodyStr2 != null) {
                                        val ui2 = parseVerifyResult(bodyStr2)
                                        addToHistory(text, null, ui2)
                                        mainHandler.post { state = ui2 }
                                    } else {
                                        val uiFail = VerifyUiState(
                                            loading = false,
                                            status = "Verification Failed",
                                            explanation = "Server Error: ${it.code}",
                                            verdict = "Error",
                                            showRetry = true
                                        )
                                        mainHandler.post { state = uiFail }
                                    }
                                }
                            }
                        })
                    }
                }
            }
        })
    }

    fun sendMedia(uri: Uri, text: String, mediaType: String, ctx: Context) {
        // ✅ Use verify for image/text, verify_media for video
        val endpoint = if (mediaType == "video") VERIFY_MEDIA_URL else VERIFY_URL

        val fileName = when (mediaType) {
            "video" -> "upload.mp4"
            "image" -> "upload.jpg"
            else -> "upload.bin"
        }

        val mimeType = when (mediaType) {
            "video" -> "video/mp4"
            "image" -> "image/jpeg"
            else -> "application/octet-stream"
        }

        state = state.copy(loading = true, status = "Uploading ${mediaType}...")
        android.util.Log.d("VerifyMedia", "Uploading $mediaType → $endpoint")

        try {
            val inputStream = ctx.contentResolver.openInputStream(uri)
            val tempFile = File.createTempFile("upload", ".tmp", ctx.cacheDir).apply {
                outputStream().use { out -> inputStream?.copyTo(out) }
            }
            android.util.Log.d("VerifyMedia", "File path: ${tempFile.absolutePath}, Size: ${tempFile.length()} bytes, MediaType: $mediaType, Text: \"${text}\"")

            val mpBuilder = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                // Only send empty string if no text, don't send placeholder for media-only
                .addFormDataPart("text", if (text.isNotBlank()) text else "")
                .addFormDataPart("language", getSupportedLanguage(ctx))
                .addFormDataPart("mode", "fast")

            // Add force_refresh only for video
            if (mediaType == "video") {
                mpBuilder.addFormDataPart("force_refresh", "true")
            }

            if (mediaType == "video") {
                mpBuilder.addFormDataPart("file", fileName, tempFile.asRequestBody(mimeType.toMediaTypeOrNull()))
            } else {
                mpBuilder.addFormDataPart("image", fileName, tempFile.asRequestBody(mimeType.toMediaTypeOrNull()))
            }

            val mp = mpBuilder.build()

            val req = Request.Builder()
                .withAuth()
                .url(endpoint)
                .post(mp)
                .build()
            postAndRender(req, text, isVideoVerification = (mediaType == "video"))
        } catch (ex: Exception) {
            val errorState = VerifyUiState(
                loading = false,
                status = "File Error",
                explanation = "Could not process ${mediaType}: ${ex.message}",
                verdict = "Error",
                showRetry = true
            )
            state = errorState
            addToHistory(input, selectedMediaUri, errorState)
        }
    }

    LaunchedEffect(initialText) {
        if (!initialText.isNullOrBlank()) sendTextOnly(initialText)
    }

    // Warm up Cloud Run to reduce first-request latency (cold start)
    LaunchedEffect(Unit) {
        warmUpBackend(client, mainHandler)
    }

    Box(modifier = Modifier.fillMaxSize().background(colors.background)) {
        Column(
            modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier.fillMaxWidth().height(64.dp).background(colors.background).padding(horizontal = 16.dp)
            ) {
                IconButton(onClick = { sidebarOpen = !sidebarOpen }, modifier = Modifier.align(Alignment.CenterStart)) {
                    Icon(imageVector = if (sidebarOpen) Icons.Rounded.Close else Icons.Rounded.Menu, contentDescription = "Menu", tint = colors.foreground)
                }
                Row(modifier = Modifier.align(Alignment.Center), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Icon(painter = painterResource(id = R.drawable.pramana_logo_black), contentDescription = null, tint = colors.foreground, modifier = Modifier.size(40.dp))
                }
            }

            AnimatedContent(
                targetState = when {
                    loadingTrending -> "loading_trending"
                    showTrending -> "trending"
                    state.loading -> "loading"
                    state.verdict.isNullOrBlank() -> "input"
                    else -> "result"
                },
                transitionSpec = { fadeIn(tween(300)) togetherWith fadeOut(tween(300)) },
                label = "page_transition"
            ) { pageState ->
                when (pageState) {
                    "loading_trending" -> LoadingScreen(status = "Loading trending claims...", colors = colors)
                    "trending" -> TrendingScreen(
                        items = trendingItems,
                        onBack = { showTrending = false; trendingItems = emptyList() },
                        onItemClick = { item ->
                            input = item.text
                            showTrending = false
                            sendTextOnly(item.text)
                        },
                        colors = colors
                    )
                    "loading" -> LoadingScreen(status = state.status, colors = colors)
                    "input" -> MainInputScreen(
                        input = input,
                        onInputChange = { input = it },
                        selectedMediaUri = selectedMediaUri,
                        selectedMediaType = selectedMediaType,
                        onPickMedia = { pickMediaLauncher.launch("*/*") },
                        onTakePhoto = {
                            when (PackageManager.PERMISSION_GRANTED) {
                                ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) -> {
                                    try {
                                        val uri = createImageFile(context)
                                        cameraImageUri.value = uri
                                        takePictureLauncher.launch(uri)
                                    } catch (ex: Exception) {
                                        android.util.Log.e("Camera", "Error creating file: ${ex.message}", ex)
                                    }
                                }
                                else -> cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                            }
                        },
                        onRemoveMedia = { selectedMediaUri = null; selectedMediaType = null },
                        onVerify = {
                            val t = input.trim()
                            if (selectedMediaUri != null && selectedMediaType != null) {
                                sendMedia(selectedMediaUri!!, t, selectedMediaType!!, context)
                            } else if (t.isNotEmpty()) {
                                // URL or plain-text: both supported by backend via text
                                sendTextOnly(t)
                            }
                        },
                        onExploreTrending = { fetchTrendingItems() },
                        colors = colors
                    )
                    "result" -> ResultScreen(
                        state = state,
                        onNewVerification = {
                            input = ""
                            selectedMediaUri = null
                            selectedMediaType = null
                            state = VerifyUiState()
                        },
                        onFeedback = { feedbackType ->
                            state.requestId?.let {
                                sendFeedback(it, feedbackType)
                            }
                        },
                        colors = colors
                    )
                }
            }
        }

        if (sidebarOpen) {
            Box(
                modifier = Modifier.fillMaxSize().zIndex(10f).background(Color.Black.copy(alpha = 0.5f))
                    .clickable(indication = null, interactionSource = remember { MutableInteractionSource() }) { sidebarOpen = false }
            )
        }

        AnimatedVisibility(
            visible = sidebarOpen,
            modifier = Modifier.fillMaxHeight().align(Alignment.CenterStart).zIndex(11f),
            enter = slideInHorizontally(tween(300)) { -it } + fadeIn(tween(300)),
            exit = slideOutHorizontally(tween(250)) { -it } + fadeOut(tween(250))
        ) {
            SearchHistorySidebar(
                history = searchHistory,
                onItemClick = { item ->
                    input = item.text
                    selectedMediaUri = item.mediaUri
                    selectedMediaType = if (item.mediaUri != null) if (item.isVideoVerification) "video" else "image" else null
                    // For restoring state, set only citationsDetailed to item.citationsDetailed
                    state = VerifyUiState(
                        loading = false, status = "Done", verdict = item.verdict,
                        explanation = item.explanation, confidence = item.confidence,
                        citationsDetailed = item.citationsDetailed, // Ensure citationsDetailed is populated for restored state
                        imageUri = item.mediaUri,
                        showRetry = false, requestId = item.requestId,
                        isVideoVerification = item.isVideoVerification,
                        deepfakeDetected = item.deepfakeDetected,
                        deepfakeConfidence = item.deepfakeConfidence
                    )
                    sidebarOpen = false
                },
                onClose = { sidebarOpen = false },
                colors = colors
            )
        }
    }
}

// All other composables (TrendingScreen, MainInputScreen, ResultScreen, etc.) follow here...

// Warm up Cloud Run to reduce first-request latency (cold start)
private fun warmUpBackend(client: OkHttpClient, mainHandler: Handler) {
    val warmupRequest = Request.Builder()
        .withAuth()
        .url("$BASE_URL/healthcheck")
        .get()
        .build()

    // Try /healthcheck; if it 404s, fall back to TRENDING_URL which is cheap
    client.newCall(warmupRequest).enqueue(object : Callback {
        override fun onFailure(call: Call, e: IOException) {
            // Fallback to trending (do nothing with response)
            val fallback = Request.Builder()
                .withAuth()
                .url(TRENDING_URL)
                .get()
                .build()
            client.newCall(fallback).enqueue(object : Callback {
                override fun onFailure(call2: Call, e2: IOException) { /* ignore */ }
                override fun onResponse(call2: Call, response2: Response) { response2.close() }
            })
        }
        override fun onResponse(call: Call, response: Response) {
            response.close()
        }
    })
}

@Composable
private fun TrendingScreen(
    items: List<TrendingItem>,
    onBack: () -> Unit,
    onItemClick: (TrendingItem) -> Unit,
    colors: ThemeColors
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            IconButton(onClick = onBack) {
                Icon(
                    imageVector = Icons.AutoMirrored.Rounded.ArrowBack,
                    contentDescription = "Back",
                    tint = colors.foreground
                )
            }

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    "Trending Claims",
                    style = MaterialTheme.typography.headlineSmall.copy(
                        fontWeight = FontWeight.Bold
                    ),
                    color = colors.foreground
                )
                Text(
                    "Most verified claims in the last 48 hours",
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.muted
                )
            }
        }

        Spacer(Modifier.height(24.dp))

        if (items.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 48.dp),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Rounded.TrendingUp,
                        contentDescription = null,
                        tint = colors.muted,
                        modifier = Modifier.size(48.dp)
                    )
                    Spacer(Modifier.height(16.dp))
                    Text(
                        "No trending claims found",
                        style = MaterialTheme.typography.bodyLarge,
                        color = colors.muted
                    )
                }
            }
        } else {
            items.forEach { item ->
                TrendingItemCard(
                    item = item,
                    onClick = { onItemClick(item) },
                    colors = colors
                )
                Spacer(Modifier.height(12.dp))
            }
        }
    }
}

@Composable
private fun TrendingItemCard(
    item: TrendingItem,
    onClick: () -> Unit,
    colors: ThemeColors
) {
    Surface(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = colors.card,
        border = BorderStroke(1.dp, colors.border)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = PrimaryDark.copy(alpha = 0.1f),
                    border = BorderStroke(1.dp, PrimaryDark.copy(alpha = 0.3f))
                ) {
                    Text(
                        "${item.count} verifications",
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontWeight = FontWeight.Bold
                        ),
                        color = PrimaryDark
                    )
                }

                Text(
                    formatTimeDetailed(parseTimestamp(item.lastSeen)),
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.muted
                )
            }

            Spacer(Modifier.height(12.dp))

            Text(
                item.text,
                style = MaterialTheme.typography.bodyLarge,
                color = colors.foreground,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis
            )

            Spacer(Modifier.height(8.dp))

            Text(
                "Tap to verify again",
                style = MaterialTheme.typography.bodySmall,
                color = colors.muted
            )
        }
    }
}

private fun parseTimestamp(timestamp: String): Long {
    return try {
        // Handle ISO 8601 with optional milliseconds
        val format = if (timestamp.contains(".")) {
            SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS", Locale.US)
        } else {
            SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
        }
        format.parse(timestamp)?.time ?: System.currentTimeMillis()
    } catch (ex: Exception) {
        System.currentTimeMillis()
    }
}

@Composable
private fun MainInputScreen(
    input: String,
    onInputChange: (String) -> Unit,
    selectedMediaUri: Uri?,
    selectedMediaType: String?,
    onPickMedia: () -> Unit,
    onTakePhoto: () -> Unit,
    onRemoveMedia: () -> Unit,
    onVerify: () -> Unit,
    onExploreTrending: () -> Unit,
    colors: ThemeColors
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("Verify Information", style = MaterialTheme.typography.headlineMedium.copy(fontWeight = FontWeight.Bold, fontSize = 28.sp), color = colors.foreground)
        Spacer(Modifier.height(8.dp))
        Text("Check claims and sources for accuracy", style = MaterialTheme.typography.bodyMedium, color = colors.muted)
        Spacer(Modifier.height(32.dp))

        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            AnimatedVisibility(
                visible = selectedMediaUri != null,
                enter = fadeIn(tween(300)) + expandVertically(tween(300)),
                exit = fadeOut(tween(300)) + shrinkVertically(tween(300))
            ) {
                Box(modifier = Modifier.fillMaxWidth()) {
                    Surface(
                        modifier = Modifier.fillMaxWidth().height(200.dp),
                        shape = RoundedCornerShape(16.dp),
                        color = colors.card,
                        border = BorderStroke(1.dp, colors.border)
                    ) {
                        if (selectedMediaType == "image") {
                            AsyncImage(model = selectedMediaUri, contentDescription = "Selected image", modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
                        } else {
                            Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize().background(Color.Black)) {
                                Icon(Icons.Rounded.Videocam, contentDescription = "Video selected", tint = Color.White, modifier = Modifier.size(48.dp))
                            }
                        }
                    }
                    IconButton(
                        onClick = onRemoveMedia,
                        modifier = Modifier.align(Alignment.TopEnd).padding(8.dp).background(Color.Black.copy(alpha = 0.6f), CircleShape)
                    ) {
                        Icon(imageVector = Icons.Rounded.Close, contentDescription = "Remove media", tint = Color.White, modifier = Modifier.size(20.dp))
                    }
                }
            }

            Surface(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp), color = colors.card, border = BorderStroke(1.dp, colors.border)) {
                Column {
                    OutlinedTextField(
                        value = input,
                        onValueChange = onInputChange,
                        modifier = Modifier.fillMaxWidth(),
                        placeholder = { Text(if (selectedMediaUri != null) "Add context or description (optional)..." else "Enter a claim or URL to verify...", color = colors.muted) },
                        colors = TextFieldDefaults.colors(
                            focusedContainerColor = Color.Transparent, unfocusedContainerColor = Color.Transparent,
                            focusedIndicatorColor = Color.Transparent, unfocusedIndicatorColor = Color.Transparent,
                            focusedTextColor = colors.foreground, unfocusedTextColor = colors.foreground, cursorColor = colors.foreground
                        ),
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                        keyboardActions = KeyboardActions(onDone = { onVerify() }),
                        minLines = 3, maxLines = 6
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                            MediaButton(onClick = onPickMedia, icon = Icons.Rounded.Image, text = if (selectedMediaUri != null) "Change" else "Add Media", isSelected = selectedMediaUri != null, colors = colors)
                            MediaButton(onClick = onTakePhoto, icon = Icons.Rounded.CameraAlt, text = "Camera", isSelected = false, colors = colors)
                        }
                        Text(
                            if (selectedMediaUri != null) "${selectedMediaType?.replaceFirstChar { it.uppercase() }} added" else "${input.length} chars",
                            style = MaterialTheme.typography.bodySmall, color = colors.muted
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(24.dp))
        CleanButton(onClick = onVerify, enabled = input.trim().isNotEmpty() || selectedMediaUri != null, text = "Verify", icon = Icons.Rounded.Search, colors = colors)
        Spacer(Modifier.height(20.dp))
        OutlineCleanButton(onClick = onExploreTrending, text = "Explore Trending", icon = Icons.Rounded.TrendingUp, colors = colors)
        Spacer(Modifier.height(24.dp))
        Text("An OrangeXAI Production.", style = MaterialTheme.typography.bodySmall, color = colors.muted, textAlign = TextAlign.Center)
    }
}

@Composable
private fun MediaButton(onClick: () -> Unit, icon: ImageVector, text: String, isSelected: Boolean, colors: ThemeColors) {
    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(8.dp),
        color = if (isSelected) colors.buttonPrimary.copy(alpha = 0.1f) else Color.Transparent,
        border = if (isSelected) null else BorderStroke(1.dp, colors.border)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(imageVector = icon, contentDescription = text, tint = if (isSelected) colors.buttonPrimary else colors.muted, modifier = Modifier.size(18.dp))
            Text(text, style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Medium), color = if (isSelected) colors.buttonPrimary else colors.muted)
        }
    }
}

@Composable
private fun ResultScreen(
    state: VerifyUiState,
    onNewVerification: () -> Unit,
    onFeedback: (String) -> Unit,
    colors: ThemeColors
) {
    val context = LocalContext.current
    var feedbackSent by remember { mutableStateOf(false) }
    var showCitations by remember { mutableStateOf(false) }

    val verdictColor = when (state.verdict?.uppercase()) {
        "TRUE" -> SuccessGreen
        "FALSE", "SUSPICIOUS" -> ErrorRed
        "MISLEADING" -> WarningYellow
        else -> Color(0xFF9CA3AF)
    }

    fun openUrl(url: String) {
        try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            context.startActivity(intent)
        } catch (ex: Exception) {
            android.util.Log.e("ResultScreen", "Error opening URL: ${ex.message}")
        }
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(20.dp)
    ) {
        Surface(
            modifier = Modifier.align(Alignment.CenterHorizontally),
            shape = RoundedCornerShape(50.dp),
            color = verdictColor.copy(alpha = 0.1f),
            border = BorderStroke(1.dp, verdictColor.copy(alpha = 0.3f))
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 20.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    imageVector = Icons.Rounded.CheckCircle,
                    contentDescription = null,
                    tint = verdictColor,
                    modifier = Modifier.size(20.dp)
                )
                Text(
                    state.verdict?.uppercase() ?: "UNKNOWN",
                    style = MaterialTheme.typography.labelLarge.copy(
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    ),
                    color = verdictColor
                )
            }
        }

        Spacer(Modifier.height(12.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center
        ) {
            Text(
                "${(state.confidence * 100).toInt()}% confidence",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.muted
            )
            Text(" · ", color = colors.muted)
            Text(
                "Just now",
                style = MaterialTheme.typography.bodyMedium,
                color = colors.muted
            )
        }

        Spacer(Modifier.height(24.dp))

        Text(
            "Confidence level",
            style = MaterialTheme.typography.labelMedium,
            color = colors.muted
        )

        Spacer(Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            LinearProgressIndicator(
                progress = { state.confidence.toFloat() },
                modifier = Modifier
                    .weight(1f)
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp)),
                color = verdictColor,
                trackColor = colors.border
            )
            Spacer(Modifier.width(12.dp))
            Text(
                "${(state.confidence * 100).toInt()}%",
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontWeight = FontWeight.Bold
                ),
                color = colors.foreground
            )
        }

        Spacer(Modifier.height(24.dp))

        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = verdictColor.copy(alpha = 0.05f),
            shape = RoundedCornerShape(12.dp),
            border = BorderStroke(1.dp, verdictColor.copy(alpha = 0.2f))
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    "Verdict Summary",
                    style = MaterialTheme.typography.labelLarge.copy(
                        fontWeight = FontWeight.Bold
                    ),
                    color = verdictColor
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    state.explanation ?: "No summary available",
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.foreground,
                    lineHeight = 22.sp
                )
            }
        }

        // Collapsible citations pane (always show toggle when citations exist)
        val citationsList = state.citationsDetailed.takeIf { it.isNotEmpty() }
        if (citationsList != null) {
            Spacer(Modifier.height(16.dp))
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = colors.card,
                shape = RoundedCornerShape(12.dp),
                border = BorderStroke(1.dp, colors.border)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        "Citations · ${citationsList.size}",
                        style = MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.Bold),
                        color = colors.foreground
                    )
                    Spacer(Modifier.height(8.dp))
                    TextButton(
                        onClick = { showCitations = !showCitations },
                        modifier = Modifier.align(Alignment.Start)
                    ) {
                        Text(
                            if (showCitations) "Hide Citations" else "Show Citations",
                            color = colors.buttonPrimary
                        )
                    }
                    AnimatedVisibility(
                        visible = showCitations,
                        enter = fadeIn() + expandVertically(),
                        exit = fadeOut() + shrinkVertically()
                    ) {
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            citationsList.forEach { (title, url) ->
                                Surface(
                                    onClick = { if (url.isNotBlank()) openUrl(url) },
                                    modifier = Modifier.fillMaxWidth(),
                                    color = colors.card,
                                    shape = RoundedCornerShape(10.dp),
                                    border = BorderStroke(1.dp, colors.border)
                                ) {
                                    Row(
                                        modifier = Modifier.padding(14.dp),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Column(modifier = Modifier.weight(1f)) {
                                            Text(
                                                title,
                                                style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
                                                color = colors.foreground,
                                                maxLines = 2,
                                                overflow = TextOverflow.Ellipsis
                                            )
                                            if (url.isNotBlank()) {
                                                Spacer(Modifier.height(4.dp))
                                                Text(
                                                    url,
                                                    style = MaterialTheme.typography.bodySmall,
                                                    color = colors.muted,
                                                    maxLines = 1,
                                                    overflow = TextOverflow.Ellipsis
                                                )
                                            }
                                        }
                                        if (url.isNotBlank()) {
                                            Icon(
                                                imageVector = Icons.Rounded.OpenInNew,
                                                contentDescription = "Open citation",
                                                tint = colors.muted,
                                                modifier = Modifier.size(18.dp)
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        val negativeVerdicts = setOf("FALSE", "MISLEADING", "SUSPICIOUS", "INCORRECT", "FAKE", "DECEPTIVE")
        val normalizedVerdict = state.verdict?.uppercase()
        val isNegativeVerdict = normalizedVerdict != null && normalizedVerdict in negativeVerdicts

        val shouldShowManipulationCard =
            isNegativeVerdict && (
                !state.manipulationTechnique.isNullOrBlank() ||
                !state.manipulationExplanation.isNullOrBlank()
            )

        // Manipulation Technique Card: show whenever backend supplies details, or verdict is negative
        if (shouldShowManipulationCard) {
            Spacer(Modifier.height(20.dp))
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = Color(0xFF1E293B).copy(alpha = 0.05f),
                shape = RoundedCornerShape(12.dp),
                border = BorderStroke(1.dp, Color(0xFF1E293B).copy(alpha = 0.2f))
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    val techniqueLabel = when {
                        !state.manipulationTechnique.isNullOrBlank() -> state.manipulationTechnique
                        normalizedVerdict != null && normalizedVerdict in negativeVerdicts -> "Not provided"
                        else -> "Unknown"
                    }
                    val explanationText = when {
                        !state.manipulationExplanation.isNullOrBlank() -> state.manipulationExplanation
                        normalizedVerdict != null && normalizedVerdict in negativeVerdicts -> "No manipulation notes returned by the backend."
                        else -> "No further explanation provided."
                    }
                    Text(
                        "Manipulation Technique: $techniqueLabel",
                        style = MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.Bold),
                        color = Color(0xFF1E293B)
                    )
                    Text(
                        explanationText,
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.foreground,
                        lineHeight = 22.sp
                    )
                    if (!state.timestamp.isNullOrBlank()) {
                        Text(
                            "Detected on: ${state.timestamp}",
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.muted
                        )
                    }
                }
            }
        }

        if (state.isVideoVerification) {
            Spacer(Modifier.height(16.dp))
            DeepfakeResultCard(state = state, colors = colors)
        }

        Spacer(Modifier.height(24.dp))

        Spacer(Modifier.height(28.dp))
        // Feedback Section
        AnimatedContent(targetState = feedbackSent, label = "feedback_transition") { hasSentFeedback ->
            if (hasSentFeedback) {
                Box(modifier = Modifier.fillMaxWidth().height(56.dp), contentAlignment = Alignment.Center) {
                    Text("Thank you for your feedback!", color = colors.muted, style = MaterialTheme.typography.bodyMedium)
                }
            } else {
                Column {
                    Text(
                        "Was this result helpful?",
                        style = MaterialTheme.typography.labelMedium,
                        color = colors.muted,
                        modifier = Modifier.align(Alignment.CenterHorizontally)
                    )
                    Spacer(Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        OutlinedButton(
                            onClick = { onFeedback("upvote"); feedbackSent = true },
                            modifier = Modifier.weight(1f).height(48.dp),
                            shape = RoundedCornerShape(12.dp),
                            border = BorderStroke(1.dp, colors.border),
                        ) {
                            Icon(Icons.Rounded.ThumbUp, contentDescription = "Helpful", tint = colors.muted)
                            Spacer(Modifier.width(8.dp))
                            Text("Helpful", color = colors.foreground)
                        }
                        OutlinedButton(
                            onClick = { onFeedback("downvote"); feedbackSent = true },
                            modifier = Modifier.weight(1f).height(48.dp),
                            shape = RoundedCornerShape(12.dp),
                            border = BorderStroke(1.dp, colors.border),
                        ) {
                            Icon(Icons.Rounded.ThumbDown, contentDescription = "Incorrect", tint = colors.muted)
                            Spacer(Modifier.width(8.dp))
                            Text("Incorrect", color = colors.foreground)
                        }
                    }
                }
            }
        }

        Spacer(Modifier.height(24.dp))
        CleanButton(onClick = onNewVerification, enabled = true, text = "New Verification", icon = Icons.Rounded.Search, colors = colors)
    }
}

@Composable
private fun DeepfakeResultCard(state: VerifyUiState, colors: ThemeColors) {
    val statusColor = if (state.deepfakeDetected) ErrorRed else SuccessGreen
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = statusColor.copy(alpha = 0.05f),
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(1.dp, statusColor.copy(alpha = 0.2f))
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Deepfake Analysis", style = MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.Bold), color = statusColor)
            Spacer(Modifier.height(12.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Status: ", style = MaterialTheme.typography.bodySmall, color = colors.muted)
                Text(if (state.deepfakeDetected) "Suspicious" else "Likely Authentic", style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold), color = statusColor)
                Spacer(Modifier.weight(1f))
                Text("Confidence: ", style = MaterialTheme.typography.bodySmall, color = colors.muted)
                Text("${(state.deepfakeConfidence * 100).toInt()}%", style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold), color = colors.foreground)
            }
        }
    }
}

@Composable
private fun SearchHistorySidebar(
    history: List<SearchHistoryItem>,
    onItemClick: (SearchHistoryItem) -> Unit,
    onClose: () -> Unit,
    colors: ThemeColors
) {
    Surface(
        modifier = Modifier
            .fillMaxHeight()
            .width(280.dp),
        color = colors.card,
        shadowElevation = 8.dp
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.pramana_logo_black),
                        contentDescription = null,
                        tint = colors.foreground,
                        modifier = Modifier.size(20.dp)
                    )
                    Text(
                        "TruthLens",
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontWeight = FontWeight.SemiBold
                        ),
                        color = colors.foreground
                    )
                }

                IconButton(onClick = onClose) {
                    Icon(
                        imageVector = Icons.Rounded.Close,
                        contentDescription = "Close sidebar",
                        tint = colors.foreground,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }

            Spacer(Modifier.height(8.dp))

            Text(
                "Recent verifications",
                style = MaterialTheme.typography.labelMedium.copy(
                    fontSize = 12.sp
                ),
                color = colors.muted,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
            )

            if (history.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        "No verifications yet",
                        color = colors.muted,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            } else {
                history.forEach { item ->
                    HistoryItem(item, onItemClick, colors)
                }
            }
        }
    }
}

@Composable
private fun HistoryItem(
    item: SearchHistoryItem,
    onClick: (SearchHistoryItem) -> Unit,
    colors: ThemeColors
) {
    val (statusColor, statusIcon) = when (item.verdict?.uppercase()) {
        "TRUE" -> SuccessGreen to Icons.Rounded.CheckCircle
        "FALSE" -> ErrorRed to Icons.Rounded.Close
        "MISLEADING" -> WarningYellow to Icons.Rounded.Warning
        else -> colors.muted to Icons.Rounded.CheckCircle
    }

    Surface(
        onClick = { onClick(item) },
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 8.dp, vertical = 2.dp),
        shape = RoundedCornerShape(8.dp),
        color = Color.Transparent
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.Top
        ) {
            Icon(
                imageVector = statusIcon,
                contentDescription = null,
                tint = statusColor,
                modifier = Modifier.size(18.dp)
            )

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    item.text.ifBlank { "Media Verification" },
                    style = MaterialTheme.typography.bodyMedium.copy(
                        fontSize = 14.sp
                    ),
                    color = colors.foreground,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    formatTimeDetailed(item.timestamp),
                    style = MaterialTheme.typography.bodySmall.copy(
                        fontSize = 12.sp
                    ),
                    color = colors.muted
                )
            }
        }
    }
}

private fun formatTimeDetailed(timestamp: Long): String {
    val now = System.currentTimeMillis()
    val diff = now - timestamp

    return when {
        diff < 60000 -> {
            val seconds = (diff / 1000).toInt()
            if (seconds < 5) "Just now" else "$seconds seconds ago"
        }
        diff < 3600000 -> {
            val minutes = (diff / 60000).toInt()
            "$minutes ${if (minutes == 1) "minute" else "minutes"} ago"
        }
        diff < 86400000 -> {
            val hours = (diff / 3600000).toInt()
            "$hours ${if (hours == 1) "hour" else "hours"} ago"
        }
        diff < 172800000 -> "1 day ago"
        diff < 604800000 -> {
            val days = (diff / 86400000).toInt()
            "$days days ago"
        }
        else -> "Long ago"
    }
}

@Composable
private fun CleanButton(
    onClick: () -> Unit,
    enabled: Boolean,
    text: String,
    icon: ImageVector,
    colors: ThemeColors
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(14.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = colors.buttonPrimary,
            contentColor = Color.White,
            disabledContainerColor = colors.border,
            disabledContentColor = colors.muted
        ),
        elevation = ButtonDefaults.buttonElevation(
            defaultElevation = 0.dp,
            pressedElevation = 0.dp
        )
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(20.dp)
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text,
            style = MaterialTheme.typography.bodyLarge.copy(
                fontWeight = FontWeight.SemiBold
            )
        )
    }
}

@Composable
private fun OutlineCleanButton(
    onClick: () -> Unit,
    text: String,
    icon: ImageVector,
    colors: ThemeColors
) {
    OutlinedButton(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(14.dp),
        border = BorderStroke(1.dp, colors.border),
        colors = ButtonDefaults.outlinedButtonColors(
            contentColor = colors.foreground
        )
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(20.dp)
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text,
            style = MaterialTheme.typography.bodyLarge.copy(
                fontWeight = FontWeight.Medium
            )
        )
    }
}

@Composable
private fun LoadingScreen(status: String, colors: ThemeColors) {
    var dotCount by remember { mutableIntStateOf(0) }

    LaunchedEffect(Unit) {
        while (true) {
            delay(1000)
            dotCount = (dotCount + 1) % 4
        }
    }

    val funMessages = listOf(
        "Fact-checking at light speed",
        "Consulting our AI detectives",
        "Cross-referencing databases",
        "Analyzing media frames",
        "Verifying claims"
    )

    var currentMessage by remember { mutableStateOf(funMessages.random()) }

    LaunchedEffect(Unit) {
        while (true) {
            delay(2500)
            currentMessage = funMessages.random()
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            CircularProgressIndicator(
                modifier = Modifier.size(56.dp),
                color = colors.buttonPrimary,
                strokeWidth = 5.dp
            )

            Spacer(Modifier.height(32.dp))

            Text(
                status + ".".repeat(dotCount),
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.Bold
                ),
                color = colors.foreground,
                textAlign = TextAlign.Center
            )

            Spacer(Modifier.height(12.dp))

            AnimatedContent(
                targetState = currentMessage,
                transitionSpec = {
                    fadeIn(tween(300)) togetherWith fadeOut(tween(300))
                },
                label = "message_animation"
            ) { message ->
                Text(
                    message,
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.muted,
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}
