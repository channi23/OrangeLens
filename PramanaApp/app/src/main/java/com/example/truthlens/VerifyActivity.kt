package com.example.truthlens

import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.example.truthlens.ui.VerifyScreen
import com.example.truthlens.ui.theme.PramanaTheme

class VerifyActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Extract text from multiple sources
        val textToVerify = intent.getStringExtra("EXTRA_TEXT_TO_VERIFY")
            ?: intent.getStringExtra("SHARED_TEXT")

        // Extract image URI
        val imageUriString = intent.getStringExtra("SHARED_IMAGE_URI")
        val imageUri = imageUriString?.let { Uri.parse(it) }

        setContent {
            PramanaTheme {
                VerifyScreen(
                    initialText = textToVerify,
                    initialImageUri = imageUri
                )
            }
        }
    }
}
