import os

import httpx

MODEL_NAME = "openai/gpt-oss-120b"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterConfigurationError(Exception):
    pass


class OpenRouterRequestError(Exception):
    pass


class OpenRouterTimeoutError(Exception):
    pass


def query_openrouter(prompt: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterConfigurationError("OPENROUTER_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    referer = os.getenv("OPENROUTER_HTTP_REFERER")
    title = os.getenv("OPENROUTER_APP_TITLE")
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-Title"] = title

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    try:
        response = httpx.post(
            OPENROUTER_CHAT_URL,
            headers=headers,
            json=payload,
            timeout=20.0,
        )
    except httpx.TimeoutException as exc:
        raise OpenRouterTimeoutError("OpenRouter request timed out") from exc
    except httpx.HTTPError as exc:
        raise OpenRouterRequestError(str(exc)) from exc

    if response.status_code >= 400:
        raise OpenRouterRequestError(
            f"OpenRouter returned status {response.status_code}: {response.text}"
        )

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise OpenRouterRequestError("OpenRouter response did not include choices")

    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise OpenRouterRequestError("OpenRouter response content was empty")

    return content.strip()
