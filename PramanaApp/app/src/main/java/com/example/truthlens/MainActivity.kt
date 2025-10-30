package com.example.truthlens

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Get shared text and image URI from intent
        val sharedText = intent?.getStringExtra("SHARED_TEXT")
        val sharedImageUriString = intent?.getStringExtra("SHARED_IMAGE_URI")

        // Navigate to VerifyActivity and pass both text and image
        val verifyIntent = Intent(this, VerifyActivity::class.java).apply {
            if (sharedText != null) {
                putExtra("SHARED_TEXT", sharedText)
            }
            if (sharedImageUriString != null) {
                putExtra("SHARED_IMAGE_URI", sharedImageUriString)
            }
        }
        startActivity(verifyIntent)

        // Finish MainActivity so user cannot go back
        finish()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)

        // Handle new intent if activity is already running
        val sharedText = intent.getStringExtra("SHARED_TEXT")
        val sharedImageUriString = intent.getStringExtra("SHARED_IMAGE_URI")

        if (sharedText != null || sharedImageUriString != null) {
            val verifyIntent = Intent(this, VerifyActivity::class.java).apply {
                if (sharedText != null) putExtra("SHARED_TEXT", sharedText)
                if (sharedImageUriString != null) putExtra("SHARED_IMAGE_URI", sharedImageUriString)
                flags = Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
            startActivity(verifyIntent)
            finish()
        }
    }
}
