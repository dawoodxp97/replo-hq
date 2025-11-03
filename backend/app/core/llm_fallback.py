# ./backend/app/core/llm_fallback.py
"""
LLM Fallback System

This module provides fallback logic to automatically try alternative LLM providers
when the primary provider fails (e.g., quota exceeded, API errors).
"""
import logging
from typing import List, Optional, Any, Tuple
from ..core.llm_providers import create_llm_provider, LLMProvider

logger = logging.getLogger(__name__)


def get_available_providers(
    user_settings,
    exclude_provider: Optional[str] = None
) -> List[Tuple[str, str, Optional[str], Optional[str]]]:
    """
    Get all available LLM providers with their API keys.
    
    Returns:
        List of tuples: (provider_type, api_key, model, base_url)
    """
    available = []
    
    # Get primary provider
    primary_provider = user_settings.llm_provider or "openai"
    
    if exclude_provider != primary_provider:
        primary_key = user_settings.llm_api_key
        # Backward compatibility with openai_api_key
        if not primary_key and primary_provider == "openai":
            primary_key = user_settings.openai_api_key
        
        if primary_provider == "ollama" or primary_key:
            available.append((
                primary_provider,
                primary_key,
                user_settings.llm_model,
                user_settings.llm_base_url
            ))
    
    # Get additional providers from llm_provider_keys
    provider_keys = user_settings.llm_provider_keys or {}
    
    for provider_type, api_key in provider_keys.items():
        if provider_type == exclude_provider:
            continue
        
        if provider_type.lower() == "ollama":
            # Ollama doesn't need API key
            available.append((
                provider_type.lower(),
                None,
                None,  # Use default model
                user_settings.llm_base_url  # Use primary base_url or default
            ))
        elif api_key and api_key.strip():
            # Provider has API key
            available.append((
                provider_type.lower(),
                api_key.strip(),
                None,  # Use default model for fallback
                None   # Use default base_url
            ))
    
    return available


async def call_llm_with_fallback(
    user_settings,
    prompt: str,
    response_format: str = "text",
    system_message: Optional[str] = None,
    max_retries: int = 3
) -> Tuple[Any, str]:
    """
    Call LLM with automatic fallback to other available providers.
    
    Args:
        user_settings: UserSettings object with LLM configuration
        prompt: The prompt to send
        response_format: "text" or "json"
        system_message: Optional system message
        max_retries: Maximum number of providers to try
        
    Returns:
        Tuple of (response, provider_name_used)
        
    Raises:
        Exception if all providers fail
    """
    # Get all available providers
    available_providers = get_available_providers(user_settings)
    
    if not available_providers:
        raise Exception("No LLM providers configured. Please add at least one API key.")
    
    logger.info(f"[Fallback] Starting LLM call with {len(available_providers)} available provider(s)")
    
    errors = []
    
    for idx, (provider_type, api_key, model, base_url) in enumerate(available_providers[:max_retries]):
        try:
            logger.info(f"[Fallback] Attempting provider {idx+1}/{len(available_providers)}: {provider_type}")
            
            # Create provider instance
            provider = create_llm_provider(
                provider_type=provider_type,
                api_key=api_key,
                model=model,
                base_url=base_url
            )
            
            # Try to generate
            response = await provider.generate(
                prompt=prompt,
                response_format=response_format,
                temperature=0.2,
                system_message=system_message
            )
            
            logger.info(f"[Fallback] ✅ Success with provider: {provider_type}")
            return response, provider_type
            
        except Exception as e:
            error_msg = str(e)
            errors.append((provider_type, error_msg))
            
            # Check if it's a quota/rate limit error
            is_quota_error = (
                "quota" in error_msg.lower() or
                "429" in error_msg or
                "insufficient_quota" in error_msg.lower() or
                "rate limit" in error_msg.lower()
            )
            
            # Check if it's a temporary service error (503, 502, 500) or timeout
            is_temporary_error = (
                "503" in error_msg or
                "502" in error_msg or
                "timed out" in error_msg.lower() or
                "timeout" in error_msg.lower() or
                "temporarily unavailable" in error_msg.lower() or
                "unavailable" in error_msg.lower() or
                "server error" in error_msg.lower() or
                "try again later" in error_msg.lower()
            )
            
            # Check if it's a connection error (should also try fallback)
            is_connection_error = (
                "cannot connect" in error_msg.lower() or
                "connection" in error_msg.lower() or
                "connection refused" in error_msg.lower()
            )
            
            if is_quota_error:
                logger.warning(f"[Fallback] ⚠️  Provider {provider_type} quota exceeded, trying next provider...")
            elif is_temporary_error:
                logger.warning(f"[Fallback] ⚠️  Provider {provider_type} temporarily unavailable or timed out, trying next provider...")
            elif is_connection_error:
                logger.warning(f"[Fallback] ⚠️  Provider {provider_type} connection failed, trying next provider...")
            else:
                logger.warning(f"[Fallback] ⚠️  Provider {provider_type} failed: {error_msg[:100]}...")
            
            # Continue to next provider
            continue
    
    # All providers failed
    error_summary = "; ".join([f"{p}: {e[:50]}" for p, e in errors])
    raise Exception(
        f"All LLM providers failed. Errors: {error_summary}. "
        f"Please check your API keys and quotas."
    )

