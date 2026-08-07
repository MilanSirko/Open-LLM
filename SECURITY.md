# Security Policy

At Open LLM, we take the security of our project and the privacy of our users very seriously. 

---

## 🔒 Supported Versions

Only the latest version on the `main` branch is actively supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| Main    | :white_check_mark: |
| < 1.0   | :x:                |

---

## 🛡️ Reporting a Vulnerability

> [!WARNING]
> **Please do NOT report security vulnerabilities through public GitHub issues.**

If you discover a potential security vulnerability or issue regarding data privacy (such as API key exposure or data leaks), please follow these steps:

1. **Private Reporting:**  
   Send an email directly to the project maintainer at **`sirkomilan570@gmail.com`**  with the subject `[SECURITY] Open-LLM Vulnerability`.

2. **Provide Details:**  
   Include as much information as possible:
   * Description of the vulnerability or security risk.
   * Steps to reproduce the issue (proof of concept, code snippets, or screenshots).
   * Potential impact of the issue.

3. **Response Time:**  
   We will acknowledge receipt of your vulnerability report within **48 hours** and provide regular updates on the progress toward a patch or resolution.

---

## 🔑 Security Best Practices for Users

* **Never commit your API keys:** Do not hardcode secret keys in public repositories or public commits.
* **Environment Variables:** Always use local `.env` files or the application's built-in settings UI (Bring Your Own Key feature) to store sensitive keys safely.
