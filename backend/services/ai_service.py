import os
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Retry configuration for transient errors
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def analyze_resume(prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    """
    Analyze resume text using Groq LLM with retry logic.
    
    Args:
        prompt: The formatted prompt to send to the LLM
        model: Groq model to use (default: llama-3.1-8b-instant)
    
    Returns:
        Raw response text from the LLM
        
    Raises:
        ValueError: If prompt is empty or API key is missing
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    try:
        client = Groq(api_key=api_key)
        logger.info(f"Sending request to Groq API using model: {model}")
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048
        )
        
        result = response.choices[0].message.content
        logger.info("Successfully received response from Groq API")
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze_resume: {e}")
        raise