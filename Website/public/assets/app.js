/* ============================================================
   Open LLM — shared vanilla JS
   Handles: navbar scroll state, scroll-reveal, copy buttons,
   count-up stats, mobile menu, and Python syntax highlighting.
   ============================================================ */

(function () {
  "use strict"

  /* ---------- Navbar scroll state ---------- */
  const nav = document.querySelector("[data-nav]")
  if (nav) {
    const onScroll = () => {
      if (window.scrollY > 12) nav.classList.add("nav-scrolled")
      else nav.classList.remove("nav-scrolled")
    }
    onScroll()
    window.addEventListener("scroll", onScroll, { passive: true })
  }

  /* ---------- Mobile menu toggle ---------- */
  const menuBtn = document.querySelector("[data-menu-btn]")
  const mobileMenu = document.querySelector("[data-mobile-menu]")
  if (menuBtn && mobileMenu) {
    menuBtn.addEventListener("click", () => {
      mobileMenu.classList.toggle("hidden")
    })
  }

  /* ---------- Scroll reveal via IntersectionObserver ---------- */
  const revealEls = document.querySelectorAll(".reveal")
  if ("IntersectionObserver" in window && revealEls.length) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible")
            io.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    )
    revealEls.forEach((el) => io.observe(el))
  } else {
    revealEls.forEach((el) => el.classList.add("is-visible"))
  }

  /* ---------- Count-up animation for stats ---------- */
  const counters = document.querySelectorAll("[data-count]")
  if (counters.length && "IntersectionObserver" in window) {
    const cObs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return
          const el = entry.target
          const target = parseFloat(el.getAttribute("data-count"))
          const suffix = el.getAttribute("data-suffix") || ""
          const decimals = (el.getAttribute("data-decimals") || "0") | 0
          const duration = 1400
          const start = performance.now()
          const step = (now) => {
            const p = Math.min((now - start) / duration, 1)
            const eased = 1 - Math.pow(1 - p, 3)
            const val = target * eased
            el.textContent = val.toFixed(decimals) + suffix
            if (p < 1) requestAnimationFrame(step)
          }
          requestAnimationFrame(step)
          cObs.unobserve(el)
        })
      },
      { threshold: 0.5 }
    )
    counters.forEach((el) => cObs.observe(el))
  }

  /* ---------- Copy to clipboard buttons ---------- */
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-copy]")
    if (!btn) return
    const sel = btn.getAttribute("data-copy")
    const source = document.querySelector(sel)
    if (!source) return
    const text = source.getAttribute("data-raw") || source.textContent
    navigator.clipboard.writeText(text.trim()).then(() => {
      const label = btn.querySelector("[data-copy-label]")
      const original = label ? label.textContent : null
      btn.classList.add("copied")
      if (label) label.textContent = "Copied!"
      setTimeout(() => {
        btn.classList.remove("copied")
        if (label && original) label.textContent = original
      }, 1600)
    })
  })

  /* ---------- Lightweight Python syntax highlighter ---------- */
  // Highlights every <code data-lang="python"> block. Keeps HTML clean:
  // author plain code, this adds VS Code Dark+ style token colors.
  const KEYWORDS = new Set([
    "from", "import", "as", "def", "return", "if", "elif", "else", "for",
    "while", "in", "not", "and", "or", "is", "None", "True", "False",
    "class", "with", "try", "except", "finally", "raise", "lambda", "yield",
    "async", "await", "pass", "break", "continue", "global", "print",
  ])

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  }

  function highlightPython(raw) {
    const lines = raw.split("\n")
    return lines
      .map((line) => {
        // full-line / trailing comments
        const commentIdx = findCommentIndex(line)
        let code = line
        let comment = ""
        if (commentIdx !== -1) {
          code = line.slice(0, commentIdx)
          comment = line.slice(commentIdx)
        }

        // tokenize the code part
        const tokenRegex =
          /("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|\b\d+\.?\d*\b|[A-Za-z_]\w*|[=+\-*/%<>!.:,()[\]{}]|\s+)/g
        let out = ""
        let m
        let prevNonSpace = ""
        while ((m = tokenRegex.exec(code)) !== null) {
          const t = m[0]
          if (/^\s+$/.test(t)) {
            out += t
            continue
          }
          if (/^("|')/.test(t)) {
            out += `<span class="tok-str">${escapeHtml(t)}</span>`
          } else if (/^\d/.test(t)) {
            out += `<span class="tok-num">${escapeHtml(t)}</span>`
          } else if (/^[A-Za-z_]\w*$/.test(t)) {
            const after = code.slice(tokenRegex.lastIndex).match(/^\s*\(/)
            if (KEYWORDS.has(t)) {
              out += `<span class="tok-kw">${t}</span>`
            } else if (after) {
              out += `<span class="tok-fn">${t}</span>`
            } else if (prevNonSpace === "." ) {
              out += `<span class="tok-var">${t}</span>`
            } else if (/^[A-Z]/.test(t)) {
              out += `<span class="tok-cls">${t}</span>`
            } else {
              out += `<span class="tok-var">${t}</span>`
            }
          } else if (/^[=+\-*/%<>!]$/.test(t)) {
            out += `<span class="tok-op">${escapeHtml(t)}</span>`
          } else {
            out += `<span class="tok-punc">${escapeHtml(t)}</span>`
          }
          prevNonSpace = t
        }

        if (comment) {
          out += `<span class="tok-com">${escapeHtml(comment)}</span>`
        }
        return out
      })
      .join("\n")
  }

  // Find index of a '#' that is not inside a string literal.
  function findCommentIndex(line) {
    let inStr = false
    let quote = ""
    for (let i = 0; i < line.length; i++) {
      const ch = line[i]
      if (inStr) {
        if (ch === quote && line[i - 1] !== "\\") inStr = false
      } else {
        if (ch === '"' || ch === "'") {
          inStr = true
          quote = ch
        } else if (ch === "#") {
          return i
        }
      }
    }
    return -1
  }

  // Minimal JSON highlighter — keys, strings, numbers, literals, punctuation.
  function highlightJson(raw) {
    const tokenRegex = /("(?:[^"\\]|\\.)*"(\s*:)?|\b-?\d+\.?\d*\b|\b(?:true|false|null)\b|[{}[\],:]|\s+)/g
    let out = ""
    let m
    while ((m = tokenRegex.exec(raw)) !== null) {
      const t = m[0]
      if (/^\s+$/.test(t)) {
        out += t
      } else if (/^"/.test(t) && m[2]) {
        // string immediately followed by a colon => object key
        const key = t.replace(/\s*:$/, "")
        out += `<span class="tok-var">${escapeHtml(key)}</span><span class="tok-punc">:</span>`
      } else if (/^"/.test(t)) {
        out += `<span class="tok-str">${escapeHtml(t)}</span>`
      } else if (/^-?\d/.test(t)) {
        out += `<span class="tok-num">${escapeHtml(t)}</span>`
      } else if (/^(true|false|null)$/.test(t)) {
        out += `<span class="tok-kw">${t}</span>`
      } else {
        out += `<span class="tok-punc">${escapeHtml(t)}</span>`
      }
    }
    return out
  }

  document.querySelectorAll('code[data-lang="python"], code[data-lang="json"]').forEach((el) => {
    const raw = el.textContent.replace(/^\n/, "").replace(/\s+$/, "")
    // store raw text for the copy button
    const shell = el.closest(".code-shell")
    if (shell) shell.setAttribute("data-raw", raw)
    el.setAttribute("data-raw", raw)
    el.innerHTML = el.getAttribute("data-lang") === "json" ? highlightJson(raw) : highlightPython(raw)
  })

  /* ---------- Year in footer ---------- */
  document.querySelectorAll("[data-year]").forEach((el) => {
    el.textContent = new Date().getFullYear()
  })
})()
