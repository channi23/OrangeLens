package com.example.truthlens.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.ui.unit.dp

val AppShapes = Shapes(
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(16.dp),
    large = RoundedCornerShape(24.dp)
)
// Add these additional shapes to your existing Shape.kt file

val EnhancedShapes = Shapes(
    extraSmall = RoundedCornerShape(4.dp),
    small = RoundedCornerShape(12.dp),
    medium = RoundedCornerShape(20.dp),
    large = RoundedCornerShape(28.dp),
    extraLarge = RoundedCornerShape(36.dp)
)

// Custom shapes for specific components
val CardShape = RoundedCornerShape(24.dp)
val ButtonShape = RoundedCornerShape(16.dp)
val InputShape = RoundedCornerShape(20.dp)
val BadgeShape = RoundedCornerShape(50.dp)
val ModalShape = RoundedCornerShape(topStart = 32.dp, topEnd = 32.dp)
