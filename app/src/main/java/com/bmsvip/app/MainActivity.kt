package com.bmsvip.app

import android.app.Activity
import android.os.Bundle
import android.graphics.Color
import android.graphics.Typeface
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.*
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.InetAddress
import java.net.URL
import java.net.Socket
import java.util.concurrent.Executors
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class MainActivity : Activity() {
    private val bg = Color.rgb(10, 14, 22)
    private val panel = Color.rgb(20, 27, 39)
    private val accent = Color.rgb(0, 220, 170)
    private val muted = Color.rgb(155, 170, 190)
    private val executor = Executors.newSingleThreadExecutor()
    private lateinit var body: LinearLayout
    private lateinit var output: TextView
    private val rootDir by lazy { File(filesDir, "BMS-VIP").apply { mkdirs() } }
    private val workspace by lazy { File(rootDir, "workspace").apply { mkdirs() } }
    private val backups by lazy { File(rootDir, "backups").apply { mkdirs() } }
    private val logFile by lazy { File(rootDir, "activity.json").apply { if (!exists()) writeText("[]") } }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        showHome()
    }

    private fun base(title: String, subtitle: String = "PRIVATE • PRACTICAL • OFFLINE-FIRST") {
        val scroll = ScrollView(this).apply { setBackgroundColor(bg) }
        val page = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(22, 28, 22, 28)
        }
        scroll.addView(page)
        val header = TextView(this).apply {
            text = "BMS VIP  /  $title"
            textSize = 23f
            setTextColor(Color.WHITE)
            typeface = Typeface.create("sans-serif", Typeface.BOLD)
        }
        page.addView(header)
        page.addView(TextView(this).apply {
            text = subtitle
            textSize = 10f
            setTextColor(accent)
            setPadding(0, 7, 0, 20)
            letterSpacing = 0.16f
        })
        body = page
        output = TextView(this).apply {
            setTextColor(Color.rgb(210, 222, 238))
            textSize = 12f
            setPadding(14, 14, 14, 14)
            setBackgroundColor(panel)
        }
        page.addView(output, LinearLayout.LayoutParams(-1, -2).apply { topMargin = 12 })
        setContentView(scroll)
    }

    private fun button(label: String, action: () -> Unit) {
        val b = Button(this).apply {
            text = label
            isAllCaps = false
            textSize = 14f
            setTextColor(Color.WHITE)
            backgroundTintList = android.content.res.ColorStateList.valueOf(panel)
            setPadding(12, 12, 12, 12)
            gravity = Gravity.CENTER_VERTICAL
            setOnClickListener { action() }
        }
        body.addView(b, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = 8 })
    }

    private fun heading(text: String) {
        body.addView(TextView(this).apply {
            this.text = text
            textSize = 14f
            setTextColor(accent)
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, 15, 0, 8)
        })
    }

    private fun field(hint: String, value: String = ""): EditText {
        val e = EditText(this).apply {
            this.hint = hint
            setText(value)
            setTextColor(Color.WHITE)
            setHintTextColor(muted)
            textSize = 14f
            setSingleLine(true)
            setPadding(14, 10, 14, 10)
            backgroundTintList = android.content.res.ColorStateList.valueOf(accent)
        }
        body.addView(e, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = 8 })
        return e
    }

    private fun result(text: String) {
        output.text = text
    }

    private fun runTask(task: () -> String) {
        result("Working…")
        executor.execute {
            val message = try { task() } catch (e: Exception) { "ERROR: ${e.message ?: e.javaClass.simpleName}" }
            runOnUiThread { result(message) }
            log("Task", message.take(160))
        }
    }

    private fun log(type: String, detail: String) {
        try {
            val arr = JSONArray(logFile.readText())
            arr.put(JSONObject().put("time", System.currentTimeMillis()).put("type", type).put("detail", detail))
            while (arr.length() > 500) arr.remove(0)
            logFile.writeText(arr.toString())
        } catch (_: Exception) {}
    }

    private fun showHome() {
        base("CONTROL CENTER", "VERSION 3.1  •  ANDROID EDITION")
        heading("SYSTEM")
        button("01  Dashboard", ::showDashboard)
        heading("NETWORK TOOLS")
        button("02  DNS lookup", ::showDns)
        button("03  Single-host TCP test", ::showTcp)
        button("04  Website status (HTTP GET)", ::showWebsite)
        button("05  Authorized API GET", ::showApi)
        heading("UTILITIES")
        button("06  JSON formatter / validator", ::showJson)
        button("07  Text utilities", ::showText)
        button("08  Workspace file manager", ::showWorkspace)
        button("09  ZIP backup manager", ::showBackups)
        button("10  Activity analytics / CSV", ::showAnalytics)
        heading("APP")
        button("Settings & app information", ::showSettings)
        result("Ready. Choose a module to begin.")
    }

    private fun backButton() = button("←  Back to dashboard", ::showHome)

    private fun showDashboard() {
        base("DASHBOARD")
        val free = rootDir.usableSpace / (1024 * 1024)
        heading("DEVICE & APP")
        result("BMS VIP 3.1\\nAndroid ${android.os.Build.VERSION.RELEASE}\\nWorkspace: ${workspace.absolutePath}\\nAvailable app storage: ${free} MB\\nNetwork tools run only when you request them.")
        backButton()
    }

    private fun showDns() {
        base("DNS LOOKUP")
        val host = field("Domain or hostname")
        button("Resolve hostname") {
            val h = host.text.toString().trim()
            if (h.isBlank()) result("Enter a hostname first.")
            else runTask { InetAddress.getAllByName(h).joinToString("\\n") { it.hostAddress } }
        }
        backButton()
    }

    private fun showTcp() {
        base("TCP TEST")
        val host = field("Host name (one host only)")
        val port = field("Port (e.g. 443)", "443")
        button("Test connection") {
            val h = host.text.toString().trim()
            val p = port.text.toString().toIntOrNull()
            if (h.isBlank() || p == null || p !in 1..65535) result("Enter a valid host and port (1–65535).")
            else runTask {
                Socket().use { s -> s.connect(java.net.InetSocketAddress(h, p), 5000); "Connection successful: $h:$p" }
            }
        }
        backButton()
    }

    private fun showWebsite() {
        base("WEBSITE STATUS")
        val address = field("https://example.com")
        button("Check website") {
            val raw = address.text.toString().trim()
            runTask {
                val u = if (raw.startsWith("http://") || raw.startsWith("https://")) raw else "https://$raw"
                val c = URL(u).openConnection() as HttpURLConnection
                c.requestMethod = "GET"; c.connectTimeout = 7000; c.readTimeout = 7000
                try { "HTTP ${c.responseCode}\\n${c.url}" } finally { c.disconnect() }
            }
        }
        backButton()
    }

    private fun showApi() {
        base("AUTHORIZED API GET")
        val address = field("API endpoint URL")
        val token = field("Optional authorization token")
        button("Send GET request") {
            val u = address.text.toString().trim()
            val t = token.text.toString()
            if (u.isBlank()) result("Enter an API URL.")
            else runTask {
                val c = URL(u).openConnection() as HttpURLConnection
                c.requestMethod = "GET"; c.connectTimeout = 8000; c.readTimeout = 8000
                if (t.isNotBlank()) c.setRequestProperty("Authorization", if (t.startsWith("Bearer ")) t else "Bearer $t")
                try {
                    val stream = if (c.responseCode < 400) c.inputStream else c.errorStream
                    "HTTP ${c.responseCode}\\n" + (stream?.bufferedReader()?.use { it.readText() } ?: "")
                } finally { c.disconnect() }
            }
        }
        backButton()
    }

    private fun showJson() {
        base("JSON TOOL")
        val input = EditText(this).apply {
            hint = "Paste JSON here"
            minLines = 6; gravity = Gravity.TOP
            setTextColor(Color.WHITE); setHintTextColor(muted)
            backgroundTintList = android.content.res.ColorStateList.valueOf(accent)
        }
        body.addView(input, LinearLayout.LayoutParams(-1, 220))
        button("Validate & format") {
            try {
                val s = input.text.toString().trim()
                val pretty = if (s.startsWith("[")) JSONArray(s).toString(2) else JSONObject(s).toString(2)
                result(pretty)
            } catch (e: Exception) { result("Invalid JSON: ${e.message}") }
        }
        backButton()
    }

    private fun showText() {
        base("TEXT UTILITIES")
        val input = field("Enter text")
        button("Count characters and words") {
            val s = input.text.toString()
            result("Characters: ${s.length}\\nWords: ${s.trim().split(Regex("\\s+")).count { it.isNotBlank() }}\\nLines: ${if (s.isEmpty()) 0 else s.lines().size}")
        }
        button("Convert to UPPERCASE") { result(input.text.toString().uppercase()) }
        button("Convert to lowercase") { result(input.text.toString().lowercase()) }
        button("Remove extra whitespace") { result(input.text.toString().trim().replace(Regex("\\s+"), " ")) }
        backButton()
    }

    private fun safeFile(name: String): File? {
        val clean = name.trim()
        if (clean.isBlank() || clean.contains("/") || clean.contains("\\\\") || clean == "." || clean == "..") return null
        return File(workspace, clean)
    }

    private fun showWorkspace() {
        base("WORKSPACE")
        val name = field("File name (no folders)")
        val content = EditText(this).apply {
            hint = "File contents"
            minLines = 4; gravity = Gravity.TOP
            setTextColor(Color.WHITE); setHintTextColor(muted)
            backgroundTintList = android.content.res.ColorStateList.valueOf(accent)
        }
        body.addView(content, LinearLayout.LayoutParams(-1, 150))
        button("Save / overwrite file") {
            val f = safeFile(name.text.toString())
            if (f == null) result("Invalid file name.")
            else try { f.writeText(content.text.toString()); result("Saved ${f.name}") } catch (e: Exception) { result("Save failed: ${e.message}") }
        }
        button("List workspace files") {
            result(workspace.listFiles()?.joinToString("\\n") { "${it.name} (${it.length()} bytes)" }?.ifBlank { "Workspace is empty." } ?: "Workspace is empty.")
        }
        button("Read file") {
            val f = safeFile(name.text.toString())
            if (f == null || !f.exists()) result("File not found.")
            else result(f.readText().take(12000))
        }
        button("Delete file") {
            val f = safeFile(name.text.toString())
            result(if (f != null && f.exists() && f.delete()) "Deleted ${f.name}" else "File not found or could not be deleted.")
        }
        backButton()
    }

    private fun showBackups() {
        base("ZIP BACKUPS")
        button("Create workspace backup") {
            runTask {
                val target = File(backups, "BMS-${System.currentTimeMillis()}.zip")
                ZipOutputStream(target.outputStream().buffered()).use { zip ->
                    workspace.walkTopDown().filter { it.isFile }.forEach { file ->
                        zip.putNextEntry(ZipEntry(file.relativeTo(workspace).path))
                        file.inputStream().use { it.copyTo(zip) }
                        zip.closeEntry()
                    }
                }
                "Backup created: ${target.name}\\n${target.length()} bytes"
            }
        }
        button("List backups") {
            result(backups.listFiles()?.joinToString("\\n") { "${it.name} (${it.length()} bytes)" }?.ifBlank { "No backups yet." } ?: "No backups yet.")
        }
        backButton()
    }

    private fun showAnalytics() {
        base("ACTIVITY ANALYTICS")
        button("View activity summary") {
            try {
                val arr = JSONArray(logFile.readText())
                val counts = mutableMapOf<String, Int>()
                for (i in 0 until arr.length()) {
                    val type = arr.getJSONObject(i).optString("type", "Other")
                    counts[type] = (counts[type] ?: 0) + 1
                }
                result("Recorded events: ${arr.length()}\\n" + counts.entries.joinToString("\\n") { "${it.key}: ${it.value}" })
            } catch (e: Exception) { result("Could not read activity log: ${e.message}") }
        }
        button("Export activity CSV") {
            try {
                val arr = JSONArray(logFile.readText())
                val file = File(rootDir, "activity-export.csv")
                file.bufferedWriter().use { w ->
                    w.appendLine("time,type,detail")
                    for (i in 0 until arr.length()) {
                        val o = arr.getJSONObject(i)
                        val detail = o.optString("detail").replace("\"", "\"\"")
                        w.appendLine("${o.optLong("time")},${o.optString("type")},\"$detail\"")
                    }
                }
                result("CSV saved inside app storage:\\n${file.absolutePath}")
            } catch (e: Exception) { result("Export failed: ${e.message}") }
        }
        backButton()
    }

    private fun showSettings() {
        base("SETTINGS & INFO")
        heading("STORAGE")
        result("All workspace files, backups, and activity logs are stored privately inside this app. Uninstalling the app removes this local data.\\n\\nNetwork tools make one user-requested request at a time. Only test systems you own or have permission to check.\\n\\nBMS VIP Android Edition 3.1")
        backButton()
    }

    override fun onDestroy() {
        executor.shutdown()
        super.onDestroy()
    }
}
