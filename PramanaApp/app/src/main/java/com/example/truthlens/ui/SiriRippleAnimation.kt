package com.example.truthlens.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import kotlin.math.min

@Composable
fun SiriRippleAnimation(
    modifier: Modifier = Modifier,
    color1: Color = Color(0xFF4A90E2), // bluish
    color2: Color = Color(0xFF50E3C2), // greenish
    circleCount: Int = 3
) {
    val transition = rememberInfiniteTransition(label = "siri_ripple")

    // Animate progress from 0f → 1f repeatedly
    val progress by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "ripple_progress"
    )

    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(220.dp) // height for animation area
    ) {
        val maxRadius = min(size.width, size.height) / 2f

        // Draw multiple expanding circles
        for (i in 0 until circleCount) {
            val fraction = (progress + i.toFloat() / circleCount) % 1f
            val radius = fraction * maxRadius
            val alpha = 1f - fraction

            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(color1.copy(alpha = alpha), color2.copy(alpha = alpha * 0.4f)),
                    center = Offset(size.width / 2, size.height / 2),
                    radius = radius
                ),
                radius = radius,
                center = Offset(size.width / 2, size.height / 2)
            )
        }
    }
}