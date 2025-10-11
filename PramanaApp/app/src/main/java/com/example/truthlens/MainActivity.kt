package com.example.truthlens

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.example.truthlens.ui.MainScreen
import com.example.truthlens.ui.theme.PramanaTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            PramanaTheme {
                MainScreen(
                    onVerifyNow = {
                        startActivity(Intent(this, VerifyActivity::class.java))
                    },
                    onOpenHistory = {
                        startActivity(Intent(this, HistoryActivity::class.java))
                    }
                )
            }
        }
    }
}
