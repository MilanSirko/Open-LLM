<div align="center">

# Open LLM

One single, OpenAI-compatible API endpoint giving you access to 100+ free models across multiple top providers!

**Features an intelligent AI router that automatically picks the best model for your prompt, full custom model support, and a constantly growing model registry. Zero code changes needed, just plug and use!**

[![CI](https://img.shields.io/github/actions/workflow/status/milansirko/open-llm/ci.yml?branch=main&label=CI)](https://github.com/milansirko/open-llm/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker Image](https://img.shields.io/badge/ghcr.io-open--llm-blue?logo=docker)](https://ghcr.io/milansirko/open-llm)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/MilanSirko/open-llm)

</div>

---
<img width="1200" height="306" alt="bannerimage(1)" src="https://github.com/user-attachments/assets/07d549de-34bb-4253-a601-ef7415f19bc6" />
You can learn more about using Open LLM on the Docs page. You can also check the model catalog page, which lists all available models. PLEASE NOTE: The list may include models that no longer exist or require payment; while we strive to keep the list up to date, we recommend using your own API keys for the providers.

## Why Open LLM exists

Free LLM access is scattered across a dozen providers, each with its own SDK, its own request shape, its own rate limits — and the free-tier landscape shifts constantly: providers add models, retire them, and tighten quotas without warning.

**Open LLM collapses all of that into one OpenAI-compatible endpoint.** Point any OpenAI client library at it, and it transparently routes across every provider you've enabled — free models by default, or your own provider keys for unlimited use on your own quota.

It's fully open source, self-hostable in a single Docker container, and built so new providers can be added in a handful of lines.

---

## What it does

- **One unified API** — a single `base_url` and API key give you access to 100+ free models across 7+ providers, with no code changes between them
- **Smart auto-routing** — `model="auto"` hands the request to a lightweight routing agent that picks the best available model for that specific message
- **Bring Your Own Key (BYOK)** — attach your own Groq/OpenRouter/Google/etc. keys per provider for unlimited, quota-isolated use; keys are encrypted at rest, never stored in plaintext
- **Self-updating catalog** — sync scripts pull each provider's live model list directly from their API, so the catalog reflects what's actually available right now instead of a list that quietly goes stale
- **Provider fallback built in** — `openrouter/auto` and the smart router both spread requests across multiple free models instead of hammering one and hitting its rate limit

---

## Quick example

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://open-llm-2fgm.onrender.com/v1",
    api_key="YOUR_OPENLLM_API_KEY"
)

response = client.chat.completions.create(
    model="openllm/auto",
    messages=[{"role": "user", "content": "Explain quantum computing simply."}]
)

print(response.choices[0].message.content)
```

Because the response follows the standard OpenAI Chat Completions shape, Open LLM works out of the box with the OpenAI SDK, most OpenAI-compatible coding agents, and anything else already built against that API.

---

## Providers
<img width="1000" height="400" alt="Use 100+ Models via an API (1)" src="https://github.com/user-attachments/assets/87502d1a-f7b9-43c2-8ab8-7fefc74cbcaf" />


| Provider | What it brings |
|---|---|
| Groq | Very fast inference, broad free-tier lineup |
| OpenRouter | 300+ models, including its own `auto` model selection |
| Google (Gemini) | Free-tier Flash models |
| Hugging Face | Routes across multiple hosted inference backends |
| OpenCode Zen | Free models curated for coding/agentic workloads |
| Cerebras | High-throughput inference on open models |
| NVIDIA NIM | Broad catalog of NVIDIA-hosted open models |

<!-- provider logos go here -->

Each provider has its own sync script that pulls the live model list on demand, so adding, removing, or refreshing models never means hand-editing a config file from memory.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/v1/chat/completions` | `POST` | Send a chat request; routes to the chosen model, `auto`, or `openrouter/auto` |
| `/models` | `GET` | List all available models, filterable by provider, tier, or kind |
| `/model/{name}` | `GET` | Get details for a single model |
| `/generate-key` | `POST` | Generate an Open LLM API key (Google sign-in required) |
| `/keys` | `GET` | List your active API keys |
| `/revokekey` | `POST` | Revoke one of your API keys |
| `/keys/provider` | `POST` / `GET` / `DELETE` | Set, list, or remove your own provider keys (BYOK) |
| `/usage` | `GET` | Check your token usage |
| `/serverinfo` | `GET` | Basic service status |

Full request/response shapes, rate limits per endpoint, and error codes are on the [docs page](https://your-openllm-instance.com/docs).

---

## Self-hosting

```bash
git clone https://github.com/YOUR_USERNAME/open-llm.git
cd open-llm
cp .env.example .env   # add your provider keys and Supabase details
docker build -t open-llm .
docker run -p 8000:8000 --env-file .env open-llm
```

Then open `http://localhost:8000/docs` to explore the API directly.

---
## Website
<img width="2559" height="1439" alt="homepage" src="https://github.com/user-attachments/assets/e3558ab0-b5a4-4755-86df-c52ee09654a3" />
**You can learn more about using Open LLM on the Docs page. You can also check the model catalog page, which lists all available models. PLEASE NOTE: The list may include models that no longer exist or require payment; while we strive to keep the list up to date, we recommend using your own API keys for the providers.**

<img width="2559" height="1439" alt="modelspage" src="https://github.com/user-attachments/assets/479e85b4-8048-42bd-aa6a-fc0ccec95d16" />

## 🔑 Bring Your Own Key (BYOK)

Our platform supports **Bring Your Own Key (BYOK)**, allowing you to use your personal API keys to run models directly under your own quotas and priorities.

<img width="2554" height="1439" alt="ownapikeypage" src="https://github.com/user-attachments/assets/f2cac558-000a-4e90-8a1e-93458b85e594" />

---

### 🛡️ Security & Privacy

Your security is our top priority. When using your own API keys, we guarantee the following protection standards:

* **Zero Server Storage:** Your API keys are never stored in our databases nor logged in any format.
* **Client-Side / Transient Handling:** Keys are strictly used in-memory solely to authenticate API requests during your active session.
* **Direct & Encrypted Communication:** All requests are transmitted over secure, encrypted (HTTPS/TLS) channels directly to the official provider endpoints (OpenAI, Anthropic, Groq, etc.).

---

### 🚀 Why Use Your Own API Key?

> [!TIP]
> Using your own API key not only enhances security but also gives you complete control and maximum performance!

1. **No Shared Rate Limits:** Bypass public queue limitations and rate limits. You get the full speed, bandwidth, and priority tier associated with your own provider account.
2. **Access to All Models:** Instantly unlock access to cutting-edge or restricted models (e.g., GPT-4o, Claude 3.5 Sonnet, Llama 3 high-tier models) as soon as they are enabled in your account.
3. **Cost Efficiency:** Pay only for what you actually consume directly to the provider (OpenAI, Groq, etc.), with zero middleman markups or platform fees.
4. **Full Data Ownership:** Requests sent via your own key adhere directly to your provider's privacy agreements (e.g., paid/enterprise tier guarantees that your data will not be used for model training).

---

### ⚙️ How to Set It Up

1. Open the **API key** menu on the platform.
2. Paste your API key obtained from your preferred provider (e.g., *OpenAI*, *Groq*).
3. Save your settings, the application will immediately begin using your key for all subsequent requests.

## Contributing

Contributions are very welcome — new provider integrations, bug fixes, documentation, or feature ideas. See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup and PR guidelines, or open an issue if something looks off.

---

## License

MIT — see [LICENSE](LICENSE).
