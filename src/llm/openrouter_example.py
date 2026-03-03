"""
OpenRouter LLM Getting Started Guide

This file demonstrates how to connect to OpenRouter LLM API.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_openrouter_client():
    """
    Initialize and return an OpenRouter client.
    
    Returns:
        OpenRouter: Configured client instance
    
    Raises:
        ValueError: If OPENROUTER_API_KEY is not set
    """
    try:
        from openrouter import OpenRouter
    except ImportError:
        raise ImportError(
            "openrouter package not installed. Run: uv add openrouter"
        )
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not found. "
            "Create a .env file with: OPENROUTER_API_KEY=your_key_here"
        )
    
    return OpenRouter(api_key=api_key)


def simple_chat_completion(prompt: str, model: str = "openrouter/aurora-alpha"):
    """
    Send a simple chat completion request to OpenRouter.
    
    Args:
        prompt: The user message/prompt
        model: The model to use (default: openrouter/aurora-alpha)
    
    Returns:
        str: The LLM response content
    """
    with get_openrouter_client() as client:
        response = client.chat.send(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content


def chat_with_system_prompt(
    user_prompt: str, 
    system_prompt: str = "You are a helpful assistant.",
    model: str = "openrouter/aurora-alpha"
):
    """
    Send a chat completion with a system prompt.
    
    Args:
        user_prompt: The user message
        system_prompt: Instructions for the AI behavior
        model: The model to use
    
    Returns:
        str: The LLM response content
    """
    with get_openrouter_client() as client:
        response = client.chat.send(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content


def check_credits():
    """
    Check your OpenRouter account credits and usage.
    
    Returns:
        dict: Credit information including:
            - credits: Total credits available
            - usage: Credits used
            - remaining: Credits remaining
    
    Raises:
        Exception: If API request fails
    """
    import httpx
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response = httpx.get(
        "https://openrouter.ai/api/v1/credits",
        headers=headers,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def print_credits_info():
    """
    Fetch and display credit information in a readable format.
    """
    try:
        credits_data = check_credits()
        
        print("=== OpenRouter Credits ===")
        print(f"Total Credits: {credits_data.get('data', {}).get('total_credits', 'N/A')}")
        print(f"Used Credits: {credits_data.get('data', {}).get('total_usage', 'N/A')}")
        
        total = credits_data.get('data', {}).get('total_credits', 0)
        used = credits_data.get('data', {}).get('total_usage', 0)
        remaining = total - used if total and used else None
        
        if remaining is not None:
            print(f"Remaining Credits: {remaining}")
            if remaining < 1:
                print("⚠️  WARNING: Low credits! Consider adding more.")
        print()
        
        return credits_data
    except Exception as e:
        print(f"Error checking credits: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # Check credits first
    print("=== Checking OpenRouter Credits ===")
    print_credits_info()
    
    # Example 1: Simple prompt
    print("=== Example 1: Simple Chat ===")
    try:
        result = simple_chat_completion("What is the capital of France?")
        print(f"Response: {result}\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Example 2: With system prompt
    print("=== Example 2: With System Prompt ===")
    try:
        result = chat_with_system_prompt(
            user_prompt="Explain quantum computing",
            system_prompt="You are a physics professor. Explain concepts simply."
        )
        print(f"Response: {result}\n")
    except Exception as e:
        print(f"Error: {e}\n")
