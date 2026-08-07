import os
import yaml
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_FILE = "models.yaml"

nvidia_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("nvidia-api"),
)


def make_slug(model_id: str) -> str:
    """
    Turns something like 'meta/llama-3.3-70b-instruct' into a clean
    slug like 'nvidia-llama-3-3-70b-instruct'.
    """
    last_part = model_id.split("/")[-1]
    slug = last_part.replace(".", "-").replace(":", "-")
    return f"nvidia-{slug}"


def fetch_nvidia_models() -> list[dict]:
    models = nvidia_client.models.list()

    entries = []
    for model in models.data:
        entry = {
            "name": model.id,
            "slug": make_slug(model.id),
            "provider": "nvidia",
            "tier": "free",   # NVIDIA NIM's free tier is evaluation-only, rate-limited (40 RPM)
            "kind": "chat",
        }
        entries.append(entry)

    return entries


def load_existing_models() -> list[dict]:
    try:
        with open(OUTPUT_FILE, "r", encoding="UTF-8") as f:
            existing = yaml.safe_load(f) or {}
            return existing.get("models", [])
    except FileNotFoundError:
        return []


def merge_models(existing: list[dict], fresh: list[dict], provider: str) -> list[dict]:
    """
    Keeps everything that isn't from the given provider, and replaces
    all entries for that provider with the freshly fetched list.
    """
    kept = [m for m in existing if m.get("provider") != provider]
    return kept + fresh


def save_models(models: list[dict]) -> None:
    with open(OUTPUT_FILE, "w", encoding="UTF-8") as f:
        yaml.dump({"models": models}, f, allow_unicode=True, sort_keys=False)


def main():
    print("Fetching models from NVIDIA NIM...")
    fresh_nvidia_models = fetch_nvidia_models()
    print(f"Found {len(fresh_nvidia_models)} NVIDIA models.")

    existing_models = load_existing_models()
    merged = merge_models(existing_models, fresh_nvidia_models, provider="nvidia")

    save_models(merged)
    print(f"Saved {len(merged)} total models to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()