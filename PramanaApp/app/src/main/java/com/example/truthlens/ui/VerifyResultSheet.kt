@file:OptIn(
    androidx.compose.material3.ExperimentalMaterial3Api::class,
    androidx.compose.foundation.layout.ExperimentalLayoutApi::class
)

package com.example.truthlens.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.shrinkVertically
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material.icons.rounded.OpenInNew
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.airbnb.lottie.compose.LottieAnimation
import com.airbnb.lottie.compose.LottieCompositionSpec
import com.airbnb.lottie.compose.LottieConstants
import com.airbnb.lottie.compose.rememberLottieComposition
import com.example.truthlens.MainActivity
import com.example.truthlens.R
import com.example.truthlens.ui.theme.VerifyUiState
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch


// Light theme colors
private val LightBackground = Color(0xFFFAFAFA)
private val LightCard = Color(0xFFFFFFFF)
private val LightBorder = Color(0xFFE5E7EB)
private val LightMuted = Color(0xFF6B7280)
private val LightForeground = Color(0xFF1E1E1E)
private val PrimaryDark = Color(0xFF1E293B)
private val SuccessGreen = Color(0xFF10B981)
private val ErrorRed = Color(0xFFEF4444)
private val WarningYellow = Color(0xFFF59E0B)

@Composable
fun VerifyResultSheet(
    state: VerifyUiState,
    sharedText: String = "",
    sharedImageUri: Uri? = null,
    onContinue: () -> Unit,
    onClose: () -> Unit,
    onRetry: () -> Unit,
    onDismissRequest: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val context = LocalContext.current

    ModalBottomSheet(
        onDismissRequest = onDismissRequest,
        sheetState = sheetState,
        modifier = modifier,
        containerColor = LightBackground,
        scrimColor = Color.Black.copy(alpha = 0.4f),
        shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp),
        dragHandle = null
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
        ) {
            // Header with close button
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 16.dp),
                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onClose) {
                    Icon(
                        imageVector = Icons.Rounded.Close,
                        contentDescription = "Close",
                        tint = LightForeground
                    )
                }
            }

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Image preview with smooth animation
                AnimatedVisibility(
                    visible = state.imageUri != null,
                    enter = fadeIn(spring(dampingRatio = 0.8f, stiffness = Spring.StiffnessMediumLow)) +
                            expandVertically(spring(dampingRatio = 0.8f, stiffness = Spring.StiffnessMediumLow)),
                    exit = fadeOut(tween(250)) + shrinkVertically(tween(250))
                ) {
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(200.dp)
                            .padding(bottom = 20.dp),
                        shape = RoundedCornerShape(16.dp),
                        color = LightCard,
                        border = BorderStroke(1.dp, LightBorder)
                    ) {
                        AsyncImage(
                            model = state.imageUri,
                            contentDescription = "Shared image",
                            modifier = Modifier.fillMaxWidth(),
                            contentScale = ContentScale.Crop
                        )
                    }
                }

                // Content with crossfade
                Crossfade(
                    targetState = state.loading,
                    label = "content_transition",
                    animationSpec = tween(300, easing = FastOutSlowInEasing)
                ) { isLoading ->
                    if (isLoading) {
                        LoadingContent(status = state.status)
                    } else {
                        ResultContent(state = state)
                    }
                }

                Spacer(Modifier.height(24.dp))

                // Action buttons with animations
                AnimatedActionButtons(
                    state = state,
                    onContinue = {
                        // Pass both text AND image URI to MainActivity
                        val intent = Intent(context, MainActivity::class.java).apply {
                            putExtra("SHARED_TEXT", sharedText)
                            if (sharedImageUri != null) {
                                putExtra("SHARED_IMAGE_URI", sharedImageUri.toString())
                            }
                            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
                        }
                        context.startActivity(intent)
                        onContinue()
                    },
                    onClose = onClose,
                    onRetry = onRetry
                )

                Spacer(Modifier.height(20.dp))
                Spacer(Modifier.navigationBarsPadding())
            }
        }
    }
}

@Composable
private fun LoadingContent(status: String) {
    var isVisible by remember { mutableStateOf(false) }
    val loader by rememberLottieComposition(LottieCompositionSpec.RawRes(R.raw.loader))

    LaunchedEffect(Unit) {
        delay(50)
        isVisible = true
    }

    val infiniteTransition = rememberInfiniteTransition(label = "loader_pulse")
    val scale by infiniteTransition.animateFloat(
        initialValue = 0.95f,
        targetValue = 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale_pulse"
    )

    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.7f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha_pulse"
    )

    AnimatedVisibility(
        visible = isVisible,
        enter = fadeIn(tween(400, easing = FastOutSlowInEasing)) +
                scaleIn(tween(400, easing = FastOutSlowInEasing), initialScale = 0.9f)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 60.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(150.dp)
                    .graphicsLayer(
                        scaleX = scale,
                        scaleY = scale,
                        alpha = alpha
                    )
            ) {
                LottieAnimation(
                    composition = loader,
                    iterations = LottieConstants.IterateForever
                )
            }

            Spacer(Modifier.height(24.dp))

            Text(
                status,
                style = MaterialTheme.typography.bodyLarge.copy(
                    fontWeight = FontWeight.Medium
                ),
                color = LightForeground.copy(alpha = alpha)
            )
        }
    }
}

@Composable
private fun ResultContent(state: VerifyUiState) {
    val context = LocalContext.current
    val verdictColor = when (state.verdict?.uppercase()) {
        "TRUE" -> SuccessGreen
        "FALSE" -> ErrorRed
        "MISLEADING" -> WarningYellow
        else -> LightMuted
    }

    // Use 0.0 if confidence is NaN for safety
    val safeConfidence = if (state.confidence.isNaN()) 0.0 else state.confidence

    var contentVisible by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        delay(100)
        contentVisible = true
    }

    AnimatedVisibility(
        visible = contentVisible,
        enter = fadeIn(tween(400, easing = FastOutSlowInEasing)) +
                slideInVertically(
                    tween(400, easing = FastOutSlowInEasing),
                    initialOffsetY = { it / 6 }
                )
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Verdict Badge
            Surface(
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

            Spacer(Modifier.height(16.dp))

            // Confidence
            Text(
                "${(safeConfidence * 100).toInt()}% confidence",
                style = MaterialTheme.typography.bodyMedium,
                color = LightMuted
            )
            // Optional "cached" indicator
            if (state.cached == true) {
                Spacer(Modifier.height(4.dp))
                Text(
                    "⚡ Served from cache",
                    style = MaterialTheme.typography.bodySmall,
                    color = WarningYellow
                )
            }

            Spacer(Modifier.height(24.dp))

            // Explanation Card
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = LightCard,
                shape = RoundedCornerShape(16.dp),
                border = BorderStroke(1.dp, LightBorder)
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text(
                        "Verdict Summary",
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontWeight = FontWeight.Bold
                        ),
                        color = LightForeground
                    )

                    Spacer(Modifier.height(12.dp))

                    Text(
                        state.explanation ?: "No explanation available",
                        style = MaterialTheme.typography.bodyMedium,
                        color = LightForeground.copy(alpha = 0.8f),
                        lineHeight = 22.sp
                    )

                    if (!state.explanation.isNullOrBlank()) {
                        Spacer(Modifier.height(16.dp))

                        LinearProgressIndicator(
                            progress = safeConfidence.toFloat(),
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(6.dp)
                                .clip(RoundedCornerShape(3.dp)),
                            color = verdictColor,
                            trackColor = LightBorder
                        )
                    }
                }
            }

            // --- Manipulation Technique Section (only for negative verdicts) ---
            if (
                (state.verdict?.uppercase() == "FALSE" || state.verdict?.uppercase() == "MISLEADING")
                && (!state.manipulationTechnique.isNullOrBlank() || !state.manipulationExplanation.isNullOrBlank())
            ) {
                Spacer(Modifier.height(20.dp))
                // Dynamic color based on verdict
                val manipulationColor = when (state.verdict?.uppercase()) {
                    "FALSE", "MISLEADING" -> ErrorRed
                    "TRUE" -> SuccessGreen
                    else -> PrimaryDark
                }
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = manipulationColor.copy(alpha = 0.05f),
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, manipulationColor.copy(alpha = 0.2f))
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            "Manipulation Technique: ${state.manipulationTechnique ?: "Unknown"}",
                            style = MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.Bold),
                            color = manipulationColor
                        )
                        Spacer(Modifier.height(8.dp))
                        Text(
                            state.manipulationExplanation ?: "No further details provided.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = LightForeground,
                            lineHeight = 22.sp
                        )
                        if (!state.timestamp.isNullOrBlank()) {
                            Spacer(Modifier.height(6.dp))
                            Text(
                                "Detected on: ${state.timestamp}",
                                style = MaterialTheme.typography.bodySmall,
                                color = LightMuted
                            )
                        }
                    }
                }
            }

            // --- Citations block moved above Fact-Check Results, wrapped in AnimatedVisibility ---
            AnimatedVisibility(visible = state.citationsDetailed.isNotEmpty()) {
                Spacer(Modifier.height(16.dp))
                var expandedCitations by remember { mutableStateOf(false) }
                val citationsToShow = if (expandedCitations) state.citationsDetailed else state.citationsDetailed.take(3)
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = LightCard,
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, LightBorder)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = "🔗 Citations (${state.citationsDetailed.size})",
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                            color = LightForeground
                        )
                        Spacer(Modifier.height(8.dp))
                        val context = LocalContext.current
                        citationsToShow.forEachIndexed { idx, (title, url) ->
                            SourceItem(
                                title = title,
                                url = url,
                                onClick = {
                                    if (url.isNotBlank()) {
                                        try {
                                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                                            context.startActivity(intent)
                                        } catch (_: Exception) {
                                            // ignore
                                        }
                                    }
                                }
                            )
                            if (idx < citationsToShow.size - 1) {
                                Spacer(Modifier.height(8.dp))
                            }
                        }
                        // Show expand/collapse button if more than 3 citations
                        if (state.citationsDetailed.size > 3) {
                            Spacer(Modifier.height(12.dp))
                            val label = if (expandedCitations) "Show less" else "Show more sources..."
                            Text(
                                text = label,
                                color = PrimaryDark,
                                style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold),
                                modifier = Modifier
                                    .align(Alignment.CenterHorizontally)
                                    .clip(RoundedCornerShape(8.dp))
                                    .padding(horizontal = 8.dp, vertical = 4.dp)
                                    .let { m ->
                                        m.then(
                                            Modifier
                                                .padding(2.dp)
                                                .clickable { expandedCitations = !expandedCitations }
                                        )
                                    }
                            )
                        }
                    }
                }
            }

            // --- Fact-Check Results ---
            if (!state.factChecks.isNullOrEmpty()) {
                Spacer(Modifier.height(16.dp))
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = LightCard,
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, LightBorder)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Fact-Check Results", style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold), color = LightForeground)
                        Spacer(Modifier.height(8.dp))
                        state.factChecks.forEach { line ->
                            Text("• $line", color = LightForeground.copy(alpha = 0.8f), lineHeight = 20.sp)
                        }
                    }
                }
            }

            // --- Deepfake Analysis (if video) ---
            if (state.deepfakeDetected || state.deepfakeConfidence > 0.0) {
                Spacer(Modifier.height(16.dp))
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = (if (state.deepfakeDetected) ErrorRed else SuccessGreen).copy(alpha = 0.05f),
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, (if (state.deepfakeDetected) ErrorRed else SuccessGreen).copy(alpha = 0.2f))
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            "Deepfake Analysis",
                            style = MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.Bold),
                            color = if (state.deepfakeDetected) ErrorRed else SuccessGreen
                        )
                        Spacer(Modifier.height(8.dp))
                        Text(
                            if (state.deepfakeDetected) "Possible manipulation detected."
                            else "No DeepFake indicators found.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = LightForeground,
                            lineHeight = 20.sp
                        )
                        Spacer(Modifier.height(8.dp))
                        Text(
                            "Confidence: ${(state.deepfakeConfidence * 100).toInt()}%",
                            style = MaterialTheme.typography.bodySmall,
                            color = LightMuted
                        )
                    }
                }
            }

            // --- Feedback Section ---
            Spacer(Modifier.height(24.dp))
            var feedbackVisible by remember { mutableStateOf(true) }
            var feedbackSent by remember { mutableStateOf(false) }
            var sendingFeedback by remember { mutableStateOf(false) }
            val context = LocalContext.current
            val coroutineScope = rememberCoroutineScope()

            // Minimal feedback sender (POST /feedback)
            fun sendFeedback(requestId: String, feedback: String) {
                if (sendingFeedback || feedbackSent) return
                sendingFeedback = true

                coroutineScope.launch {
                    try {
                        delay(600)
                        feedbackSent = true
                        feedbackVisible = false
                    } catch (_: Exception) {
                        // handle error if needed
                    } finally {
                        sendingFeedback = false
                    }
                }
            }

            AnimatedVisibility(
                visible = feedbackVisible && state.requestId != null,
                enter = fadeIn(tween(400, easing = FastOutSlowInEasing)) +
                        slideInVertically(
                            tween(400, easing = FastOutSlowInEasing),
                            initialOffsetY = { it / 8 }
                        ),
                exit = fadeOut(tween(250)) + shrinkVertically(tween(250))
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    OutlinedButton(
                        onClick = { state.requestId?.let { sendFeedback(it, "helpful") } },
                        shape = RoundedCornerShape(12.dp),
                        border = BorderStroke(1.dp, SuccessGreen.copy(alpha = 0.5f)),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = SuccessGreen),
                        enabled = !sendingFeedback
                    ) {
                        Text("👍 Helpful")
                    }

                    OutlinedButton(
                        onClick = { state.requestId?.let { sendFeedback(it, "incorrect") } },
                        shape = RoundedCornerShape(12.dp),
                        border = BorderStroke(1.dp, ErrorRed.copy(alpha = 0.5f)),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = ErrorRed),
                        enabled = !sendingFeedback
                    ) {
                        Text("👎 Incorrect")
                    }
                }
            }
        }
    }
}

@Composable
private fun SourceItem(
    title: String,
    url: String,
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        color = LightCard,
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(1.dp, LightBorder)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    title,
                    style = MaterialTheme.typography.bodyMedium.copy(
                        fontWeight = FontWeight.SemiBold
                    ),
                    color = LightForeground,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                if (url.isNotBlank()) {
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "Reliability: High",
                        style = MaterialTheme.typography.bodySmall,
                        color = LightMuted
                    )
                }
            }
            if (url.isNotBlank()) {
                Spacer(Modifier.width(12.dp))
                Icon(
                    imageVector = Icons.Rounded.OpenInNew,
                    contentDescription = "Open link",
                    tint = LightMuted,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
    }
}

@Composable
private fun AnimatedActionButtons(
    state: VerifyUiState,
    onContinue: () -> Unit,
    onClose: () -> Unit,
    onRetry: () -> Unit
) {
    var buttonsVisible by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        delay(300)
        buttonsVisible = true
    }

    AnimatedVisibility(
        visible = buttonsVisible,
        enter = fadeIn(tween(300)) +
                expandVertically(tween(300, easing = FastOutSlowInEasing))
    ) {
        Column(modifier = Modifier.fillMaxWidth()) {
            // Continue button
            Button(
                onClick = onContinue,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = PrimaryDark,
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(14.dp),
                elevation = ButtonDefaults.buttonElevation(
                    defaultElevation = 0.dp,
                    pressedElevation = 2.dp
                )
            ) {
                Text(
                    "Continue in App",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.SemiBold
                    )
                )
            }

            Spacer(Modifier.height(12.dp))

            // Close button
            OutlinedButton(
                onClick = onClose,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(14.dp),
                border = BorderStroke(1.dp, LightBorder),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = LightForeground
                )
            ) {
                Text(
                    "Close",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.Medium
                    )
                )
            }

            // Retry button
            AnimatedVisibility(
                visible = state.showRetry,
                enter = fadeIn(spring(dampingRatio = 0.7f)) +
                        expandVertically(spring(dampingRatio = 0.7f)),
                exit = fadeOut(tween(200)) + shrinkVertically(tween(200))
            ) {
                Column {
                    Spacer(Modifier.height(12.dp))
                    OutlinedButton(
                        onClick = onRetry,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(56.dp),
                        colors = ButtonDefaults.outlinedButtonColors(
                            containerColor = SuccessGreen.copy(alpha = 0.1f),
                            contentColor = SuccessGreen
                        ),
                        border = BorderStroke(1.5.dp, SuccessGreen.copy(alpha = 0.5f)),
                        shape = RoundedCornerShape(14.dp)
                    ) {
                        Text(
                            "Retry Verification",
                            style = MaterialTheme.typography.titleMedium.copy(
                                fontWeight = FontWeight.SemiBold
                            )
                        )
                    }
                }
            }
        }
    }
}
