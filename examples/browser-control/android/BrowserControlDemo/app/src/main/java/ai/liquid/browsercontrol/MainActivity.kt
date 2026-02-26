package ai.liquid.browsercontrol

import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Main Activity demonstrating on-device browser control with LFM2-350M.
 *
 * NOTE: This is a demo scaffold. To enable actual inference:
 * 1. Add LEAP SDK dependency to build.gradle.kts
 * 2. Place a GGUF model in assets/ or download at runtime
 * 3. Uncomment the LlmInference calls in BrowserAgent
 */
class MainActivity : AppCompatActivity() {

    private lateinit var agent: BrowserAgent
    private lateinit var etGoal: EditText
    private lateinit var etDom: EditText
    private lateinit var tvAction: TextView
    private lateinit var btnRun: Button
    private lateinit var progressBar: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        etGoal = findViewById(R.id.etGoal)
        etDom = findViewById(R.id.etDom)
        tvAction = findViewById(R.id.tvAction)
        btnRun = findViewById(R.id.btnRun)
        progressBar = findViewById(R.id.progressBar)

        // Initialize agent (loads model from assets)
        lifecycleScope.launch {
            initAgent()
        }

        btnRun.setOnClickListener {
            val goal = etGoal.text.toString().trim()
            val dom = etDom.text.toString().trim()
            if (goal.isNotEmpty() && dom.isNotEmpty()) {
                runInference(goal, dom)
            }
        }
    }

    private suspend fun initAgent() {
        withContext(Dispatchers.IO) {
            // For demo: use mock agent (no actual model loaded)
            agent = BrowserAgent.createMock(this@MainActivity)
        }
        btnRun.isEnabled = true
        tvAction.text = "Model ready. Enter a goal and DOM content to run inference."
    }

    private fun runInference(goal: String, dom: String) {
        btnRun.isEnabled = false
        progressBar.visibility = View.VISIBLE
        tvAction.text = "Running inference..."

        lifecycleScope.launch {
            val action = withContext(Dispatchers.IO) {
                agent.executeStep(dom, goal)
            }
            tvAction.text = "Action: $action"
            btnRun.isEnabled = true
            progressBar.visibility = View.GONE
        }
    }
}
