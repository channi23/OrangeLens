package com.example.truthlens.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.airbnb.lottie.compose.LottieAnimation
import com.airbnb.lottie.compose.LottieCompositionSpec
import com.airbnb.lottie.compose.LottieConstants
import com.airbnb.lottie.compose.rememberLottieComposition
import com.example.truthlens.R
import com.example.truthlens.ui.theme.VerdictFalse
import com.example.truthlens.ui.theme.VerdictMisleading
import com.example.truthlens.ui.theme.VerdictTrue
import com.example.truthlens.ui.theme.VerdictUnknown

@Composable
fun LoaderBlock(status: String, modifier: Modifier = Modifier) {
    val composition by rememberLottieComposition(LottieCompositionSpec.RawRes(R.raw.loader))
    Column(
        modifier = modifier
            .fillMaxWidth()
            .height(300.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        LottieAnimation(
            composition = composition,
            iterations = LottieConstants.IterateForever
        )
        Spacer(Modifier.height(12.dp))
        Text(status, style = MaterialTheme.typography.bodyMedium, color = Color.Gray)
    }
}

@Composable
fun VerdictPill(verdict: String, modifier: Modifier = Modifier) {
    val color = when (verdict.lowercase()) {
        "true" -> VerdictTrue
        "false" -> VerdictFalse
        "misleading" -> VerdictMisleading
        else -> VerdictUnknown
    }
    Surface(color = color, shape = RoundedCornerShape(50), shadowElevation = 6.dp, modifier = modifier) {
        Text(
            text = verdict.uppercase(),
            color = Color.White,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            style = MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.Bold)
        )
    }
}

@Composable
fun ResultCard(state: VerifyUI, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors()
    ) {
        Column(Modifier.padding(16.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(
                    text = "Verification Result",
                    style = MaterialTheme.typography.titleLarge
                )
                val conf = (state.confidence ?: 0.0) * 100
                Text(text = "${conf.toInt()}%", style = MaterialTheme.typography.bodyMedium)
            }

            Spacer(Modifier.height(8.dp))
            HorizontalDivider()
            Spacer(Modifier.height(8.dp))

            state.explanation?.let {
                Text(text = it, style = MaterialTheme.typography.bodyLarge)
            }

            if (state.citations.isNotEmpty()) {
                Spacer(Modifier.height(12.dp))
                Text("Citations", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(8.dp))
                state.citations.forEach { (title, _) ->
                    AssistChip(
                        onClick = { /* open URL via Intent if desired */ },
                        label = {
                            Text(
                                text = title,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        },
                        colors = AssistChipDefaults.assistChipColors()
                    )
                    Spacer(Modifier.height(6.dp))
                }
            }
        }
    }
}

