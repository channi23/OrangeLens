package com.example.truthlens.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.OpenInNew
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.airbnb.lottie.compose.LottieAnimation
import com.airbnb.lottie.compose.LottieCompositionSpec
import com.airbnb.lottie.compose.LottieConstants
import com.airbnb.lottie.compose.rememberLottieComposition
import com.example.truthlens.R
import com.example.truthlens.ui.theme.VerifyUiState
import kotlinx.coroutines.delay

// Shared dark theme colors (consistent with VerifyResultSheet)
private val ComponentCardBackground = Color(0xFF242424)
private val ComponentCardElevated = Color(0xFF2A2A2A)
private val ComponentTextPrimary = Color(0xFFE8E8E8)
private val ComponentTextSecondary = Color(0xFFB0B0B0)
private val ComponentBorderColor = Color(0xFF3A3A3A)

@Composable
private fun getVerdictColor(verdict: String?): Color {
    return when (verdict?.lowercase()) {
        "true" -> Color(0xFF4CAF50)
        "false" -> Color(0xFFF44336)
        "misleading" -> Color(0xFFFF9800)
        else -> Color(0xFF9E9E9E)
    }
}

@Composable
fun LoaderBlock(status: String, modifier: Modifier = Modifier) {
    val composition by rememberLottieComposition(LottieCompositionSpec.RawRes(R.raw.loader))

    val infiniteTransition = rememberInfiniteTransition(label = "loaderPulse")
    val scale by infiniteTransition.animateFloat(
        initialValue = 0.95f,
        targetValue = 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scalePulse"
    )

    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alphaPulse"
    )

    Column(
        modifier = modifier
            .fillMaxWidth()
            .height(300.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(
            modifier = Modifier
                .scale(scale)
                .graphicsLayer(alpha = alpha)
        ) {
            LottieAnimation(
                composition = composition,
                iterations = LottieConstants.IterateForever,
                modifier = Modifier.size(180.dp)
            )
        }
        Spacer(Modifier.height(16.dp))
        Text(
            status,
            style = MaterialTheme.typography.bodyMedium.copy(
                fontWeight = FontWeight.Medium,
                letterSpacing = 0.3.sp
            ),
            color = ComponentTextSecondary.copy(alpha = alpha)
        )
    }
}

@Composable
fun VerdictPill(verdict: String, modifier: Modifier = Modifier) {
    val color = getVerdictColor(verdict)

    Surface(
        modifier = modifier,
        color = color.copy(alpha = 0.15f),
        shape = RoundedCornerShape(100.dp),
        shadowElevation = 4.dp,
        border = BorderStroke(1.dp, color.copy(alpha = 0.3f))
    ) {
        Text(
            text = verdict.uppercase(),
            color = color,
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 12.dp),
            style = MaterialTheme.typography.labelMedium.copy(
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.2.sp
            )
        )
    }
}

@Composable
fun ResultCard(state: VerifyUiState, modifier: Modifier = Modifier) {
    val verdictColor = getVerdictColor(state.verdict)

    val infiniteTransition = rememberInfiniteTransition(label = "glow")
    val glowAlpha by infiniteTransition.animateFloat(
        initialValue = 0.6f,
        targetValue = 0.9f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "glowAlpha"
    )

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        var heroVisible by remember { mutableStateOf(false) }
        LaunchedEffect(state.verdict) {
            delay(50)
            heroVisible = true
        }

        AnimatedVisibility(
            visible = heroVisible,
            enter = fadeIn(
                animationSpec = tween(400, easing = FastOutSlowInEasing)
            ) + expandVertically(
                animationSpec = tween(400, easing = FastOutSlowInEasing)
            ),
            exit = fadeOut() + shrinkVertically()
        ) {
            HeroVerdictCard(
                verdict = state.verdict,
                verdictColor = verdictColor,
                glowAlpha = glowAlpha
            )
        }

        var contentVisible by remember { mutableStateOf(false) }
        LaunchedEffect(state.explanation) {
            delay(200)
            contentVisible = true
        }

        AnimatedVisibility(
            visible = contentVisible,
            enter = fadeIn(
                animationSpec = tween(400, delayMillis = 100, easing = FastOutSlowInEasing)
            ) + slideInVertically(
                initialOffsetY = { it / 4 },
                animationSpec = tween(400, delayMillis = 100, easing = FastOutSlowInEasing)
            )
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                // Explanation card
                if (!state.explanation.isNullOrBlank()) {
                    ContentCard(
                        verdictColor = verdictColor,
                        delay = 0
                    ) {
                        ModernSectionHeader(title = "Analysis", verdictColor = verdictColor)
                        Spacer(Modifier.height(12.dp))
                        Text(
                            text = state.explanation,
                            style = MaterialTheme.typography.bodyLarge.copy(
                                lineHeight = 26.sp,
                                fontSize = 15.sp,
                                letterSpacing = 0.15.sp,
                                fontWeight = FontWeight.Normal
                            ),
                            color = ComponentTextPrimary.copy(alpha = 0.9f)
                        )
                    }
                }

                // Sources card
                if (state.citations.isNotEmpty()) {
                    ContentCard(
                        verdictColor = verdictColor,
                        delay = 100
                    ) {
                        ModernSectionHeader(
                            title = "Sources · ${state.citations.size}",
                            verdictColor = verdictColor
                        )
                        Spacer(Modifier.height(12.dp))
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            state.citations.forEachIndexed { index, (title, url) ->
                                AnimatedSourceItem(
                                    title = title,
                                    url = url,
                                    verdictColor = verdictColor,
                                    delay = index * 50
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun HeroVerdictCard(
    verdict: String?,
    verdictColor: Color,
    glowAlpha: Float
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = verdictColor,
        shape = RoundedCornerShape(24.dp),
        shadowElevation = 12.dp
    ) {
        Box {
            Box(
                modifier = Modifier
                    .matchParentSize()
                    .background(
                        brush = Brush.verticalGradient(
                            colors = listOf(
                                Color.White.copy(alpha = 0.12f),
                                Color.Transparent,
                                Color.Black.copy(alpha = 0.25f)
                            )
                        )
                    )
            )

            Box(
                modifier = Modifier
                    .matchParentSize()
                    .background(
                        brush = Brush.radialGradient(
                            colors = listOf(
                                Color.Transparent,
                                Color.White.copy(alpha = 0.08f * glowAlpha)
                            ),
                            radius = 1000f
                        )
                    )
            )

            Column(
                modifier = Modifier.padding(28.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = verdict?.uppercase() ?: "UNKNOWN",
                            style = MaterialTheme.typography.displaySmall.copy(
                                fontWeight = FontWeight.Black,
                                fontSize = 36.sp,
                                letterSpacing = (-1).sp
                            ),
                            color = Color.White
                        )

                        Spacer(Modifier.height(6.dp))

                        Text(
                            text = "Verification Complete",
                            style = MaterialTheme.typography.bodyMedium.copy(
                                fontWeight = FontWeight.Medium,
                                letterSpacing = 0.5.sp
                            ),
                            color = Color.White.copy(alpha = 0.85f)
                        )
                    }

                    Box(
                        modifier = Modifier
                            .size(64.dp)
                            .graphicsLayer(alpha = glowAlpha)
                            .background(
                                color = Color.White.copy(alpha = 0.2f),
                                shape = CircleShape
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Box(
                            modifier = Modifier
                                .size(48.dp)
                                .background(Color.White, CircleShape)
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun ContentCard(
    verdictColor: Color,
    delay: Int,
    content: @Composable ColumnScope.() -> Unit
) {
    var visible by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        delay(delay.toLong())
        visible = true
    }

    AnimatedVisibility(
        visible = visible,
        enter = fadeIn(
            animationSpec = tween(300, easing = FastOutSlowInEasing)
        ) + slideInVertically(
            initialOffsetY = { it / 8 },
            animationSpec = tween(300, easing = FastOutSlowInEasing)
        )
    ) {
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = ComponentCardBackground,
            shape = RoundedCornerShape(20.dp),
            shadowElevation = 4.dp
        ) {
            Box {
                Box(
                    modifier = Modifier
                        .matchParentSize()
                        .background(
                            brush = Brush.verticalGradient(
                                colors = listOf(
                                    verdictColor.copy(alpha = 0.05f),
                                    Color.Transparent
                                )
                            )
                        )
                )
                Column(modifier = Modifier.padding(20.dp)) {
                    content()
                }
            }
        }
    }
}

@Composable
fun ModernSectionHeader(title: String, verdictColor: Color) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(3.dp, 20.dp)
                .background(verdictColor, RoundedCornerShape(2.dp))
        )
        Spacer(Modifier.width(10.dp))
        Text(
            title,
            style = MaterialTheme.typography.titleMedium.copy(
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.2.sp
            ),
            color = ComponentTextPrimary
        )
    }
}

@Composable
fun AnimatedSourceItem(
    title: String?,
    url: String?,
    verdictColor: Color,
    delay: Int
) {
    var visible by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        delay(delay.toLong())
        visible = true
    }

    val uriHandler = LocalUriHandler.current

    AnimatedVisibility(
        visible = visible,
        enter = fadeIn(
            animationSpec = tween(250, easing = FastOutSlowInEasing)
        ) + slideInVertically(
            initialOffsetY = { it / 6 },
            animationSpec = tween(250, easing = FastOutSlowInEasing)
        )
    ) {
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clickable(enabled = !url.isNullOrBlank()) {
                    url?.let { uriHandler.openUri(it) }
                },
            color = ComponentCardElevated,
            shape = RoundedCornerShape(12.dp),
            border = BorderStroke(1.dp, ComponentBorderColor)
        ) {
            Row(
                modifier = Modifier.padding(16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = title ?: "Source",
                        style = MaterialTheme.typography.bodyMedium.copy(
                            fontWeight = FontWeight.SemiBold,
                            letterSpacing = 0.1.sp
                        ),
                        color = ComponentTextPrimary,
                        maxLines = 2
                    )
                    if (!url.isNullOrBlank()) {
                        Spacer(Modifier.height(4.dp))
                        Text(
                            text = url,
                            style = MaterialTheme.typography.bodySmall,
                            color = verdictColor.copy(alpha = 0.7f),
                            maxLines = 1
                        )
                    }
                }

                if (!url.isNullOrBlank()) {
                    Spacer(Modifier.width(12.dp))
                    Icon(
                        imageVector = Icons.Rounded.OpenInNew,
                        contentDescription = "Open link",
                        tint = verdictColor.copy(alpha = 0.7f),
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
        }
    }
}
