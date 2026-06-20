"""Shared LLM initialization for agents."""

from langchain_aws import ChatBedrockConverse
from dotenv import load_dotenv
import os

load_dotenv()


def get_llm(temperature=0.1):
    """Get a Bedrock LLM instance for agent use."""
    return ChatBedrockConverse(
        model="us.amazon.nova-micro-v1:0",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        temperature=temperature,
        max_tokens=1000,
    )
