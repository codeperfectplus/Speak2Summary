# cython: language_level=3
import json
import os
import re
import socket
from typing import Any, Dict, Optional
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from transmeet import generate_meeting_minutes_from_transcript, generate_mind_map_from_transcript
from transmeet.utils.general_utils import get_logger

logger = get_logger(__name__)


def _default_local_llm_url() -> Optional[str]:
    configured_url = os.getenv("LOCAL_LLM_API_URL", "").strip()
    return configured_url or None


def _local_llm_timeout_seconds() -> float:
    configured_timeout = os.getenv("LOCAL_LLM_REQUEST_TIMEOUT", "900").strip()
    try:
        timeout = float(configured_timeout)
        if timeout <= 0:
            raise ValueError
        return timeout
    except ValueError:
        logger.warning(
            "Invalid LOCAL_LLM_REQUEST_TIMEOUT '%s'; falling back to 900 seconds",
            configured_timeout,
        )
        return 900.0


def _normalize_lmstudio_endpoint(base_url: Optional[str]) -> str:
    base_url = base_url or _default_local_llm_url()
    if not base_url:
        return "http://localhost:1234/v1/chat/completions"

    url = base_url.rstrip("/")
    if url.endswith("/v1/chat/completions"):
        return url
    if url.endswith("/v1"):
        return f"{url}/chat/completions"
    return f"{url}/v1/chat/completions"


def _normalize_ollama_endpoint(base_url: Optional[str]) -> str:
    base_url = base_url or _default_local_llm_url()
    if not base_url:
        return "http://localhost:11434/api/chat"

    url = base_url.rstrip("/")
    if url.endswith("/api/chat"):
        return url
    if url.endswith("/api"):
        return f"{url}/chat"
    return f"{url}/api/chat"


def _post_json(endpoint: str, payload: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    timeout_seconds = _local_llm_timeout_seconds()

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib_request.Request(endpoint, data=data, headers=headers, method="POST")
    try:
        with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""
        raise RuntimeError(f"HTTP {exc.code} calling {endpoint}: {body}") from exc
    except socket.timeout as exc:
        raise RuntimeError(
            f"Timed out after {int(timeout_seconds)}s calling {endpoint}. "
            "Increase LOCAL_LLM_REQUEST_TIMEOUT or use a faster model."
        ) from exc
    except URLError as exc:
        if isinstance(exc.reason, socket.timeout):
            raise RuntimeError(
                f"Timed out after {int(timeout_seconds)}s calling {endpoint}. "
                "Increase LOCAL_LLM_REQUEST_TIMEOUT or use a faster model."
            ) from exc
        raise RuntimeError(f"Unable to reach {endpoint}: {exc.reason}") from exc


def _get_lmstudio_content(response: Dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise RuntimeError("LM Studio response did not contain choices")

    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise RuntimeError("LM Studio response did not contain message content")
    return content.strip()


def _get_ollama_content(response: Dict[str, Any]) -> str:
    message = response.get("message") or {}
    content = message.get("content")
    if not content:
        raise RuntimeError("Ollama response did not contain message content")
    return content.strip()


def _extract_json_object(raw_text: str) -> Dict[str, Any]:
    text = raw_text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\\s*", "", text)
        text = re.sub(r"\\s*```$", "", text)

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        parsed = json.loads(snippet)
        if isinstance(parsed, dict):
            return parsed

    raise RuntimeError("Could not parse JSON object from local model response")


def _local_chat_completion(
    llm_client: str,
    llm_model: str,
    system_prompt: str,
    user_prompt: str,
    llm_base_url: Optional[str] = None,
    llm_api_key: Optional[str] = None,
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    if llm_client == "lmstudio":
        endpoint = _normalize_lmstudio_endpoint(llm_base_url)
        payload = {
            "model": llm_model,
            "messages": messages,
            "temperature": 0.2,
            "stream": False,
        }
        response = _post_json(endpoint, payload, llm_api_key)
        return _get_lmstudio_content(response)

    if llm_client == "ollama":
        endpoint = _normalize_ollama_endpoint(llm_base_url)
        payload = {
            "model": llm_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        response = _post_json(endpoint, payload, llm_api_key)
        return _get_ollama_content(response)

    raise RuntimeError(f"Unsupported local client '{llm_client}'")


def generate_meeting_minutes_with_provider(
    transcript: str,
    llm_client: str,
    llm_model: str,
    llm_base_url: Optional[str] = None,
    llm_api_key: Optional[str] = None,
) -> str:
    if llm_client in {"lmstudio", "ollama"}:
        system_prompt = (
            "You generate clear, concise meeting minutes in markdown. "
            "Use sections: Executive Summary, Key Discussion Points, Decisions Made, "
            "Action Items, Risks and Blockers, and Next Steps."
        )
        user_prompt = (
            "Create polished meeting minutes from the transcript below. "
            "Use bullet points where useful and keep factual accuracy.\n\n"
            f"Transcript:\n{transcript}"
        )
        return _local_chat_completion(
            llm_client,
            llm_model,
            system_prompt,
            user_prompt,
            llm_base_url,
            llm_api_key,
        )

    return generate_meeting_minutes_from_transcript(
        transcript,
        llm_client=llm_client,
        llm_model=llm_model,
    )


def generate_mind_map_with_provider(
    transcript: str,
    llm_client: str,
    llm_model: str,
    llm_base_url: Optional[str] = None,
    llm_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    if llm_client in {"lmstudio", "ollama"}:
        system_prompt = (
            "You return strict JSON only, no markdown. "
            "Generate a hierarchical meeting mind map."
        )
        user_prompt = (
            "From the transcript below, return only a JSON object shaped like:\n"
            "{\n"
            "  \"Root Topic\": \"Meeting Title\",\n"
            "  \"Section\": {\n"
            "    \"Subtopic\": [\"point 1\", \"point 2\"]\n"
            "  }\n"
            "}\n"
            "Use concise keys and meaningful grouping.\n\n"
            f"Transcript:\n{transcript}"
        )

        raw_response = _local_chat_completion(
            llm_client,
            llm_model,
            system_prompt,
            user_prompt,
            llm_base_url,
            llm_api_key,
        )
        parsed_response = _extract_json_object(raw_response)
        if "Root Topic" not in parsed_response:
            parsed_response["Root Topic"] = "Meeting Mind Map"
        return parsed_response

    return generate_mind_map_from_transcript(
        transcript,
        llm_client=llm_client,
        llm_model=llm_model,
    )
