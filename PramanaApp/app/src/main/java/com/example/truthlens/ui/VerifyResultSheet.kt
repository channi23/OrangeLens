@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.example.truthlens.ui

import android.net.Uri
import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.airbnb.lottie.compose.*
import com.example.truthlens.R
import com.example.truthlens.ui.theme.*

data class VerifyUI(
    val loading: Boolean = false,
    val status: String = "Idle",
    val verdict: String? = null,
    val explanation: String? = null,
    val confidence: Double? = null,
    val citations: List<Pair<String, String>> = emptyList(),
    val imageUri: Uri? = null,
    val showRetry: Boolean = false
)

@Composable
fun VerifyResultSheet(
    state: VerifyUI,
    onContinue: () -> Unit,
    onClose: () -> Unit,
    onRetry: () -> Unit,
    onDismissRequest: () -> Unit,
    modifier: Modifier = Modifier
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val siriGlow by rememberLottieComposition(LottieCompositionSpec.RawRes(R.raw.siri_glow_border))

    ModalBottomSheet(
        onDismissRequest = onDismissRequest,
        sheetState = sheetState,
        modifier = modifier.fillMaxHeight(0.9f)
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.TopCenter
        ) {
            // 🔥 Full-screen Siri Glow when loading
            if (state.loading) {
                LottieAnimation(
                    composition = siriGlow,
                    iterations = LottieConstants.IterateForever,
                    modifier = Modifier
                        .fillMaxSize()
                        .graphicsLayer(
                            scaleX = 1.4f, // wider
                            scaleY = 1.4f  // taller
                        )
                )
            }

            // Foreground content
            Scaffold(
                bottomBar = {
                    Column(
                        Modifier
                            .padding(16.dp)
                            .navigationBarsPadding()
                    ) {
                        Button(
                            onClick = onContinue,
                            modifier = Modifier.fillMaxWidth(),
                            colors = ButtonDefaults.buttonColors(containerColor = VerdictTrue)
                        ) { Text("Continue in App") }

                        Spacer(Modifier.height(8.dp))

                        OutlinedButton(
                            onClick = onClose,
                            modifier = Modifier.fillMaxWidth()
                        ) { Text("Close") }

                        AnimatedVisibility(visible = state.showRetry) {
                            Column(Modifier.fillMaxWidth()) {
                                Spacer(Modifier.height(8.dp))
                                Button(
                                    onClick = onRetry,
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = ButtonDefaults.buttonColors(containerColor = VerdictMisleading)
                                ) { Text("Retry") }
                            }
                        }
                    }
                }
            ) { innerPadding ->
                Column(
                    modifier = Modifier
                        .padding(innerPadding)
                        .verticalScroll(rememberScrollState())
                        .padding(horizontal = 20.dp, vertical = 12.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    AnimatedVisibility(
                        visible = state.imageUri != null,
                        enter = fadeIn() + slideInVertically(),
                        exit = fadeOut() + slideOutVertically()
                    ) {
                        AsyncImage(
                            model = state.imageUri,
                            contentDescription = "Shared image",
                            modifier = Modifier
                                .fillMaxWidth()
                                .heightIn(min = 120.dp, max = 220.dp)
                                .clip(RoundedCornerShape(16.dp)),
                            contentScale = ContentScale.Fit
                        )
                    }

                    Spacer(Modifier.height(12.dp))

                    AnimatedVisibility(
                        visible = !state.loading && !state.verdict.isNullOrBlank(),
                        enter = scaleIn(initialScale = 0.8f) + fadeIn(),
                        exit = scaleOut() + fadeOut()
                    ) {
                        VerdictPill(verdict = state.verdict ?: "UNKNOWN")
                    }

                    Spacer(Modifier.height(16.dp))

                    Crossfade(targetState = state.loading, label = "loader_xfade") { isLoading ->
                        if (isLoading) {
                            Card(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .heightIn(min = 320.dp), // stretch card taller when loading
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                            ) {
                                LoaderContents(status = state.status)
                            }
                        } else {
                            Card(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .wrapContentHeight(),
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                            ) {
                                ResultContents(state = state)
                            }
                        }
                    }

                    Spacer(Modifier.height(100.dp))
                }
            }
        }
    }
}

@Composable
private fun LoaderContents(status: String) {
    val loader by rememberLottieComposition(LottieCompositionSpec.RawRes(R.raw.loader))
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        LottieAnimation(
            composition = loader,
            iterations = LottieConstants.IterateForever,
            modifier = Modifier.size(200.dp) // ⬆️ bigger loader
        )
        Spacer(Modifier.height(16.dp))
        Text(
            status,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
        )
    }
}

@Composable
private fun ResultContents(state: VerifyUI) {
    Column {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Verification Result", style = MaterialTheme.typography.titleLarge)
            val conf = (state.confidence ?: 0.0) * 100
            Text("${conf.toInt()}%", style = MaterialTheme.typography.bodyMedium)
        }

        Spacer(Modifier.height(8.dp))
        HorizontalDivider()
        Spacer(Modifier.height(8.dp))

        state.explanation?.let {
            Text(it, style = MaterialTheme.typography.bodyLarge)
        }

        if (state.citations.isNotEmpty()) {
            Spacer(Modifier.height(12.dp))
            Text("Citations", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(8.dp))
            state.citations.forEach { (title, _) ->
                AssistChip(
                    onClick = { /* open url */ },
                    label = {
                        Text(
                            text = title,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                )
                Spacer(Modifier.height(6.dp))
            }
        }
    }
}

@Composable
private fun VerdictPill(verdict: String) {
    val color = when (verdict.lowercase()) {
        "true" -> VerdictTrue
        "false" -> VerdictFalse
        "misleading" -> VerdictMisleading
        else -> VerdictUnknown
    }
    Surface(
        color = color,
        shape = RoundedCornerShape(50),
        tonalElevation = 4.dp,
        shadowElevation = 6.dp,
        modifier = Modifier.animateContentSize()
    ) {
        Text(
            text = verdict.uppercase(),
            color = MaterialTheme.colorScheme.onPrimary,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            style = MaterialTheme.typography.labelLarge
        )
    }
}