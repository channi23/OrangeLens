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

// --- Premium Monochrome Palette ---

// Core Colors
private val Onyx = Color(0xFF101113)
private val Charcoal = Color(0xFF1D1E20)
private val Slate = Color(0xFF8A8F98)
private val Frost = Color(0xFFF4F4F4)
private val PureWhite = Color(0xFFFFFFFF)

// Glass Effect Colors
private val LightGlass = PureWhite.copy(alpha = 0.65f)
private val DarkGlass = Charcoal.copy(alpha = 0.75f)

// Accent for specific actions (e.g., Retry button)
private val AccentOrange = Color(0xFFFF9F0A)


private val LightColors = lightColorScheme(
    primary = Onyx,
    onPrimary = Frost,
    secondary = Charcoal,
    onSecondary = Frost,
    tertiary = AccentOrange,
    onTertiary = Onyx,
    background = Frost,
    onBackground = Onyx,
    surface = PureWhite,
    onSurface = Onyx,
    surfaceVariant = LightGlass, // For light mode glassmorphism
    onSurfaceVariant = Onyx
)

private val DarkColors = darkColorScheme(
    primary = Frost,
    onPrimary = Onyx,
    secondary = Slate,
    onSecondary = Onyx,
    tertiary = AccentOrange,
    onTertiary = Onyx,
    background = Onyx,
    onBackground = Frost,
    surface = Charcoal,
    onSurface = Frost,
    surfaceVariant = DarkGlass, // For dark mode glassmorphism
    onSurfaceVariant = Frost
)

@Composable
fun PramanaTheme(
    useDarkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false, // Disable dynamic color for a consistent brand feel
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

// Add this enhanced dark color scheme to your existing Theme.kt file

// Premium Dark Mode Color Scheme for Modern UI
private val EnhancedDarkColors = darkColorScheme(
    primary = Color(0xFF00D4FF),           // CyanPulse
    onPrimary = Color(0xFF0A0B0D),         // DeepSpace
    primaryContainer = Color(0xFF1A1B23),   // VoidBlack
    onPrimaryContainer = Color(0xFFE8EAED), // FrostWhite

    secondary = Color(0xFFBF5AF2),         // PurpleShimmer
    onSecondary = Color(0xFF0A0B0D),
    secondaryContainer = Color(0xFF22242E), // CharcoalMist
    onSecondaryContainer = Color(0xFFE8EAED),

    tertiary = Color(0xFF00FF94),          // ElectricGreen
    onTertiary = Color(0xFF0A0B0D),
    tertiaryContainer = Color(0xFF2F3240),  // SlateFog
    onTertiaryContainer = Color(0xFFE8EAED),

    error = Color(0xFFFF2D55),             // NeonRed
    onError = Color(0xFF0A0B0D),
    errorContainer = Color(0xFF3E1F23),
    onErrorContainer = Color(0xFFFFDAD6),

    background = Color(0xFF0A0B0D),        // DeepSpace
    onBackground = Color(0xFFE8EAED),      // FrostWhite

    surface = Color(0xFF13141A),           // DarkMatter
    onSurface = Color(0xFFE8EAED),
    surfaceVariant = Color(0xFF22242E),    // CharcoalMist
    onSurfaceVariant = Color(0xFF9B9FAF),  // MoonGlow

    outline = Color(0xFF4A4D5E),           // GhostGray
    outlineVariant = Color(0xFF2F3240),    // SlateFog

    inverseSurface = Color(0xFFE8EAED),
    inverseOnSurface = Color(0xFF0A0B0D),
    inversePrimary = Color(0xFF006B85),

    surfaceTint = Color(0xFF00D4FF),
    scrim = Color(0xFF000000)
)

// You can replace or add this alongside your existing PramanaTheme:
@Composable
fun EnhancedPramanaTheme(
    useDarkTheme: Boolean = true, // Default to dark for modern aesthetic
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (useDarkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        useDarkTheme -> EnhancedDarkColors
        else -> LightColors // Use your existing light scheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = EnhancedShapes, // Use the enhanced shapes
        content = content
    )
}

annotation class Theme
