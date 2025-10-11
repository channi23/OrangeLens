package com.example.truthlens.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

// Premium Brand Colors
val DeepNavy = Color(0xFF0A192F)
val EmeraldGreen = Color(0xFF2E7D32)
val GoldenAccent = Color(0xFFFFC107)
val SoftGray = Color(0xFFB0BEC5)
val OffWhite = Color(0xFFF9FAFB)
val PremiumBlack = Color(0xFF0D1117) // modern dark background

val LightColors = lightColorScheme(
    primary = EmeraldGreen,
    onPrimary = Color.White,
    secondary = DeepNavy,
    onSecondary = Color.White,
    tertiary = GoldenAccent,
    onTertiary = Color.Black,
    background = OffWhite,
    onBackground = DeepNavy,
    surface = Color.White,
    onSurface = DeepNavy
)

val DarkColors = darkColorScheme(
    primary = EmeraldGreen,
    onPrimary = Color.White, // ✅ better contrast
    secondary = SoftGray,
    onSecondary = Color.Black,
    tertiary = GoldenAccent, // ✅ consistent accent
    onTertiary = Color.Black,
    background = PremiumBlack, // ✅ modern premium dark
    onBackground = OffWhite,
    surface = Color(0xFF161B22), // subtle elevated surface
    onSurface = OffWhite
)

@Composable
fun PramanaTheme(
    useDarkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (useDarkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        useDarkTheme -> DarkColors
        else -> LightColors
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content
    )
}