package com.example.truthlens

import android.app.Activity
import android.content.Intent
import android.os.Bundle

/**
 * An invisible activity that receives selected text from the Android system's
 * context menu (via ACTION_PROCESS_TEXT) and forwards it to the main
 * VerifyActivity to be processed.
 */
class ProcessTextActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 1. Get the selected text from the intent that started this activity.
        //    This is the text the user highlighted.
        val selectedText = intent.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)

        // 2. Check if the text is not null or empty to avoid launching the app for no reason.
        if (!selectedText.isNullOrBlank()) {
            // 3. Create an intent to launch our main verification activity (VerifyActivity).
            val verifyIntent = Intent(this, VerifyActivity::class.java).apply {
                // 4. Pass the selected text along to VerifyActivity using a unique key.
                putExtra("EXTRA_TEXT_TO_VERIFY", selectedText.toString())
                // 5. These flags ensure that if VerifyActivity is already open, it's brought
                //    to the front, otherwise a new one is created.
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
            // 6. Launch the VerifyActivity with the text.
            startActivity(verifyIntent)
        }

        // 7. Immediately finish this invisible activity so the user never sees it.
        finish()
    }
}
