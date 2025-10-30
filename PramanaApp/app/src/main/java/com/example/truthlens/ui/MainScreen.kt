@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.example.truthlens.ui

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Verified
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
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
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay

// Dark Gray Color Palette
private val DarkBackground = Color(0xFF0F0F0F)
private val CardBackground = Color(0xFF1A1A1A)
private val SurfaceDark = Color(0xFF2D2D2D)
private val AccentColor = Color(0xFF4A90E2)
private val TextPrimary = Color(0xFFE8E8E8)
private val TextSecondary = Color(0xFFA0A0A0)
private val BorderColor = Color(0xFF404040)

@Composable
fun MainScreen(
    onVerifyNow: () -> Unit
) {
    Scaffold(
        containerColor = DarkBackground
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Subtle animated background
            AnimatedBackground()

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(32.dp),
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Animated Logo/Icon
                PulsingTechIcon()

                Spacer(Modifier.height(40.dp))

                // App Name
                Text(
                    text = "PRAMANA",
                    style = MaterialTheme.typography.displayLarge.copy(
                        fontWeight = FontWeight.Black,
                        fontSize = 64.sp,
                        letterSpacing = (-2).sp
                    ),
                    color = TextPrimary,
                    textAlign = TextAlign.Center
                )

                Spacer(Modifier.height(16.dp))

                // Animated tagline
                TypewriterText(
                    text = "Truth Verification Engine",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.Medium,
                        letterSpacing = 0.5.sp
                    ),
                    color = TextSecondary
                )

                Spacer(Modifier.height(80.dp))

                // Primary Tech Button
                HolographicButton(
                    onClick = onVerifyNow,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(68.dp),
                    text = "INITIATE VERIFICATION",
                    icon = Icons.Outlined.Verified,
                    isPrimary = true
                )
            }
        }
    }
}

@Composable
private fun AnimatedBackground() {
    val infiniteTransition = rememberInfiniteTransition(label = "background")

    val pulse1 by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(10000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse1"
    )

    val pulse2 by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(15000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse2"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
    ) {
        // Subtle gradient overlays
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    brush = Brush.radialGradient(
                        colors = listOf(
                            SurfaceDark.copy(alpha = 0.1f * pulse1),
                            Color.Transparent,
                            CardBackground.copy(alpha = 0.05f * pulse2),
                            Color.Transparent
                        ),
                        center = Offset(
                            x = 0.4f * pulse1,
                            y = 0.6f * pulse2
                        ),
                        radius = 600f
                    )
                )
        )

        // Subtle grid pattern
        SubtleGrid()
    }
}

@Composable
private fun SubtleGrid() {
    val infiniteTransition = rememberInfiniteTransition(label = "grid")

    val gridOffset by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 100f,
        animationSpec = infiniteRepeatable(
            animation = tween(25000, easing = LinearEasing)
        ),
        label = "grid_move"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                brush = Brush.verticalGradient(
                    colors = listOf(
                        Color.Transparent,
                        BorderColor.copy(alpha = 0.02f),
                        Color.Transparent
                    )
                )
            )
    )
}

@Composable
private fun PulsingTechIcon() {
    val infiniteTransition = rememberInfiniteTransition(label = "tech_icon")

    val scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "icon_scale"
    )

    val glow by infiniteTransition.animateFloat(
        initialValue = 0.2f,
        targetValue = 0.4f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "icon_glow"
    )

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier.size(120.dp)
    ) {
        // Outer glow
        Box(
            modifier = Modifier
                .size(100.dp)
                .scale(scale)
                .blur(20.dp)
                .background(
                    brush = Brush.radialGradient(
                        colors = listOf(
                            AccentColor.copy(alpha = glow),
                            Color.Transparent
                        )
                    ),
                    shape = CircleShape
                )
        )

        // Icon container
        Surface(
            modifier = Modifier.size(80.dp),
            shape = CircleShape,
            color = SurfaceDark,
            tonalElevation = 8.dp,
            shadowElevation = 4.dp
        ) {
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier.background(
                    brush = Brush.verticalGradient(
                        colors = listOf(
                            SurfaceDark,
                            CardBackground
                        )
                    )
                )
            ) {
                // Verification icon
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .background(
                            brush = Brush.linearGradient(
                                colors = listOf(AccentColor, AccentColor.copy(alpha = 0.8f))
                            ),
                            shape = RoundedCornerShape(8.dp)
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        "✓",
                        color = TextPrimary,
                        style = MaterialTheme.typography.titleLarge.copy(
                            fontWeight = FontWeight.Black
                        )
                    )
                }
            }
        }
    }
}

@Composable
private fun TypewriterText(text: String, style: androidx.compose.ui.text.TextStyle, color: Color) {
    var displayedText by remember { mutableStateOf("") }
    var currentIndex by remember { mutableStateOf(0) }

    LaunchedEffect(text) {
        while (currentIndex < text.length) {
            displayedText += text[currentIndex]
            currentIndex++
            delay(50) // Typing speed
        }
    }

    Text(
        text = displayedText,
        style = style,
        color = color,
        textAlign = TextAlign.Center
    )
}

@Composable
private fun HolographicButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    text: String,
    icon: ImageVector,
    isPrimary: Boolean
) {
    val infiniteTransition = rememberInfiniteTransition(label = "button_glow")

    val glowAlpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.6f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "button_glow_alpha"
    )

    Box(modifier = modifier) {
        // Subtle glow effect for primary button
        if (isPrimary) {
            Box(
                modifier = Modifier
                    .matchParentSize()
                    .blur(15.dp)
                    .background(
                        brush = Brush.linearGradient(
                            colors = listOf(
                                AccentColor.copy(alpha = glowAlpha * 0.3f),
                                AccentColor.copy(alpha = glowAlpha * 0.2f)
                            )
                        ),
                        shape = RoundedCornerShape(16.dp)
                    )
            )
        }

        // Main button
        Button(
            onClick = onClick,
            modifier = Modifier.matchParentSize(),
            colors = ButtonDefaults.buttonColors(
                containerColor = if (isPrimary) SurfaceDark else Color.Transparent,
                contentColor = TextPrimary
            ),
            shape = RoundedCornerShape(16.dp),
            elevation = ButtonDefaults.buttonElevation(
                defaultElevation = if (isPrimary) 8.dp else 2.dp,
                pressedElevation = if (isPrimary) 12.dp else 4.dp
            ),
            border = if (!isPrimary) ButtonDefaults.outlinedButtonBorder.copy(
                brush = Brush.linearGradient(
                    colors = listOf(BorderColor.copy(alpha = 0.6f), BorderColor.copy(alpha = 0.6f))
                )
            ) else null
        ) {
            Row(
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(Modifier.width(12.dp))
                Text(
                    text = text,
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.SemiBold,
                        letterSpacing = 0.5.sp
                    )
                )
            }
        }

        // Subtle animated border for primary button
        if (isPrimary) {
            Box(
                modifier = Modifier
                    .matchParentSize()
                    .clip(RoundedCornerShape(16.dp))
                    .background(
                        brush = Brush.sweepGradient(
                            colors = listOf(
                                Color.Transparent,
                                AccentColor.copy(alpha = 0.4f),
                                AccentColor.copy(alpha = 0.4f),
                                Color.Transparent
                            )
                        )
                    )
            )
        }
    }
}