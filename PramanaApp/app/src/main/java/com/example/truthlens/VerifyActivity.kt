package com.example.truthlens

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.example.truthlens.ui.VerifyScreen
import com.example.truthlens.ui.theme.PramanaTheme

class VerifyActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val initial = intent.getStringExtra("claim_text")
        setContent {
            PramanaTheme {
                VerifyScreen(initialText = initial)
            }
        }
    }
}
