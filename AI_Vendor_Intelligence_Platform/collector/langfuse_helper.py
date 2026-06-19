"""Thin wrapper around the Langfuse SDK for tracing LLM calls in the collector layer."""

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

_client = None  # module-level singleton


def get_client():
    """Return a Langfuse client, or None if credentials are not configured."""
    global _client

    if _client is not None:
        return _client

    if not _PUBLIC_KEY or not _SECRET_KEY:
        return None

    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=_PUBLIC_KEY,
            secret_key=_SECRET_KEY,
            host=_HOST,
        )
        return _client
    except Exception as exc:
        print(f"WARNING: Could not initialise Langfuse client: {exc}")
        return None


def trace_llm_call(
    trace_name: str,
    input_text: str,
    output_text: str,
    model_name: str,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Create a Langfuse trace with a single generation span.

    Returns the trace_id string, or None if Langfuse is not configured.
    """
    client = get_client()
    if client is None:
        return None

    metadata = metadata or {}

    try:
        trace = client.trace(
            name=trace_name,
            tags=list(metadata.keys()),
            metadata=metadata,
        )

        trace.generation(
            name=f"{trace_name}-generation",
            model=model_name,
            input=input_text,
            output=output_text,
            metadata=metadata,
        )

        client.flush()
        return trace.id

    except Exception as exc:
        print(f"WARNING: Langfuse trace failed ({trace_name}): {exc}")
        return None


def trace_signal_classification(
    company_name: str,
    headline: str,
    signal_type: str,
    importance_score: int,
    model_name: str,
) -> str | None:
    """Convenience wrapper for tracing a signal classification LLM call.

    Returns the trace_id string, or None if Langfuse is not configured.
    """
    input_text = f"Classify the following headline for {company_name}:\n\n{headline}"
    output_text = (
        f"signal_type={signal_type}, importance_score={importance_score}"
    )
    metadata = {
        "company_name": company_name,
        "signal_type": signal_type,
        "importance_score": importance_score,
    }

    return trace_llm_call(
        trace_name="signal-classification",
        input_text=input_text,
        output_text=output_text,
        model_name=model_name,
        metadata=metadata,
    )


if __name__ == "__main__":
    client = get_client()
    if client is None:
        print(
            "Langfuse client is not configured.\n"
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in your .env file.\n"
            f"  LANGFUSE_PUBLIC_KEY : {'set' if _PUBLIC_KEY else 'MISSING'}\n"
            f"  LANGFUSE_SECRET_KEY : {'set' if _SECRET_KEY else 'MISSING'}\n"
            f"  LANGFUSE_HOST       : {_HOST}"
        )
    else:
        trace_id = trace_llm_call(
            trace_name="langfuse-connection-test",
            input_text="Is the Langfuse integration working?",
            output_text="Yes — test trace received successfully.",
            model_name="test",
            metadata={"source": "langfuse_helper.__main__"},
        )
        if trace_id:
            print(f"Langfuse connection OK. Test trace ID: {trace_id}")
            print(f"View it at: {_HOST}/traces/{trace_id}")
        else:
            print("Langfuse client initialised but trace submission failed.")
            print("Check the WARNING messages above for details.")
