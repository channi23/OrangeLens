package com.example.truthlens

import android.content.Context
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.example.truthlens.ui.VerifyScreen
import com.example.truthlens.ui.theme.PramanaTheme
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream

class VerifyActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Extract text from multiple sources
        val textToVerify = intent.getStringExtra("EXTRA_TEXT_TO_VERIFY")
            ?: intent.getStringExtra("SHARED_TEXT")

        // Extract image URI
        val imageUriString = intent.getStringExtra("SHARED_IMAGE_URI")
        val imageUri = imageUriString?.let { Uri.parse(it) }

        // Convert content URI to a file in cache directory if imageUri is present
        val imageFileUri = imageUri?.let { uri ->
            getFileFromUri(this, uri)?.let { file ->
                Uri.fromFile(file)
            }
        }

        setContent {
            PramanaTheme {
                VerifyScreen(
                    initialText = textToVerify,
                    initialImageUri = imageFileUri
                )
            }
        }
    }

    private fun getFileFromUri(context: Context, uri: Uri): File? {
        return try {
            val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
            inputStream?.use { input ->
                val tempFile = File.createTempFile("temp_image", null, context.cacheDir)
                FileOutputStream(tempFile).use { output ->
                    input.copyTo(output)
                }
                tempFile
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
}
