// Minimal zero-dependency static file server for the Open LLM site.
const http = require("http")
const fs = require("fs")
const path = require("path")

const PORT = process.env.PORT || 3000
const ROOT = path.join(__dirname, "public")
const REPO_ROOT = path.join(__dirname, "..")

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
}

const server = http.createServer((req, res) => {
  let urlPath = decodeURIComponent(req.url.split("?")[0] || "/")
  if (urlPath === "/") urlPath = "/index.html"

  // Normalize the request URL and join safely to the public root.
  const normalizedUrl = path.posix.normalize(urlPath)
  const safeUrl = normalizedUrl.replace(/^\/+/, "")

  let filePath = path.join(ROOT, safeUrl)
  const allowedYaml = path.join(REPO_ROOT, "models.yaml")
  if (safeUrl === "models.yaml") {
    filePath = allowedYaml
  }

  if (!path.extname(filePath) && fs.existsSync(filePath + ".html")) {
    filePath += ".html"
  }

  const isPublicFile = !path.relative(ROOT, filePath).startsWith("..")
  if (!isPublicFile && filePath !== allowedYaml) {
    res.writeHead(403)
    res.end("Forbidden")
    return
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { "Content-Type": "text/html; charset=utf-8" })
      res.end("<h1>404 - Not Found</h1>")
      return
    }
    const ext = path.extname(filePath).toLowerCase()
    res.writeHead(200, {
      "Content-Type": MIME[ext] || "application/octet-stream",
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "strict-origin-when-cross-origin",
    })
    res.end(data)
  })
})

server.on("error", (err) => {
  if (err.code === "EADDRINUSE") {
    console.error(`[open-llm] Port ${PORT} is already in use.`)
    console.error(`  → Open http://localhost:${PORT} in your browser (a server may already be running).`)
    console.error(`  → Or use a different port:  $env:PORT=3001; npm run dev`)
    process.exit(1)
  }
  throw err
})

server.listen(PORT, () => {
  console.log(`[open-llm] Static server running at http://localhost:${PORT}`)
})
