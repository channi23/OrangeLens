package com.example.truthlens

import android.content.Intent
import android.os.Bundle
import android.widget.EditText
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.example.truthlens.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Set welcome text
        binding.appTitle.text = "Welcome to Pramana!"

        // Handle Verify button click → open VerifyActivity
        binding.verifyButton.setOnClickListener {
            val intent = Intent(this, VerifyActivity::class.java)
            startActivity(intent)
        }

        // Handle FAB short click → open VerifyActivity
        binding.fabVerify.setOnClickListener {
            val intent = Intent(this, VerifyActivity::class.java)
            startActivity(intent)
        }

        // Handle FAB long press → quick verify dialog
        binding.fabVerify.setOnLongClickListener {
            showQuickVerifyDialog()
            true
        }
    }

    // Quick verify popup dialog
    private fun showQuickVerifyDialog() {
        val input = EditText(this).apply {
            hint = "Enter text to verify"
            setPadding(32, 32, 32, 32)
        }

        AlertDialog.Builder(this)
            .setTitle("Quick Verify")
            .setView(input)
            .setPositiveButton("Verify") { _, _ ->
                val claim = input.text.toString().trim()
                if (claim.isNotEmpty()) {
                    // Pass text directly to VerifyActivity
                    val intent = Intent(this, VerifyActivity::class.java)
                    intent.putExtra("claim_text", claim)
                    startActivity(intent)
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
}