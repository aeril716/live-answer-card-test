import os
import requests
from dotenv import load_dotenv

load_dotenv()

USE_MOCK: bool = True

def fast_complete(prompt: str, max_tokens: int = 200) -> str:
    """
    Completes a prompt using a fast model provider, with a fallback mechanism.
    
    Args:
        prompt (str): The input prompt to be completed.
        max_tokens (int): The maximum number of tokens to generate. Defaults to 200.
        
    Returns:
        str: The generated completion text.
    """
    print(f"ENTER fast_complete | prompt={str(prompt)[:80]!r} | max_tokens={max_tokens}")
    
    if USE_MOCK:
        result = "mocked response"
        print(f"EXIT fast_complete | provider=MOCK | result={result!r}")
        return result

    configs = [
        (
            os.getenv("FAST_MODEL_PROVIDER"),
            os.getenv("FAST_MODEL_NAME"),
            os.getenv("FAST_MODEL_BASE_URL"),
            os.getenv("FAST_MODEL_API_KEY"),
        ),
        (
            os.getenv("FALLBACK_MODEL_PROVIDER"),
            os.getenv("FALLBACK_MODEL_NAME"),
            os.getenv("FALLBACK_MODEL_BASE_URL"),
            os.getenv("FALLBACK_MODEL_API_KEY"),
        )
    ]

    result = ""
    served_by = "NONE"

    for provider, model, url, key in configs:
        if not (provider and model and url and key):
            continue
            
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            }
            
            base = url.rstrip("/")
            if not base.endswith("/chat/completions"):
                base += "/chat/completions"
            resp = requests.post(base, headers=headers, json=payload, timeout=0.2)
            resp.raise_for_status()
            data = resp.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                result = data["choices"][0].get("message", {}).get("content", "")
            else:
                result = data.get("response", str(data))
                
            served_by = provider
            break
            
        except Exception:
            result = ""
            continue

    print(f"EXIT fast_complete | provider={served_by} | result={result!r}")
    return result

if __name__ == "__main__":
    print(fast_complete("hi"))