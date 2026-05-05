"""LLM service for routing requests to different language models."""

import logging
import time
from typing import Optional, Dict, Any, Tuple
from enum import Enum

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Available LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    LOCAL = "local"


class LLMService:
    """Service for interfacing with LLM providers."""

    def __init__(self):
        self.openai_api_key = settings.openai_api_key
        self.gemini_api_key = settings.gemini_api_key

    async def call_openai(
        self,
        prompt: str,
        model: str = settings.openai_model,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> Tuple[str, int, float]:
        """
        Call OpenAI API.
        
        Returns:
            (response_text, total_tokens, latency_ms)
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            tokens = data["usage"]["total_tokens"]
            latency_ms = (time.time() - start_time) * 1000
            
            logger.info(f"OpenAI call successful: {tokens} tokens, {latency_ms:.2f}ms")
            return text, tokens, latency_ms
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def call_gemini(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> Tuple[str, int, float]:
        """
        Call Gemini API.
        
        Returns:
            (response_text, total_tokens, latency_ms)
        """
        if not self.gemini_api_key:
            raise ValueError("Gemini API key not configured")

        start_time = time.time()
        
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_api_key)
        
        try:
            model = genai.GenerativeModel(settings.gemini_model)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            
            text = response.text
            # Gemini doesn't provide token count in the same way, estimate it
            tokens = len(prompt.split()) + len(text.split())
            latency_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Gemini call successful: ~{tokens} tokens, {latency_ms:.2f}ms")
            return text, tokens, latency_ms
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def call_local_model(
        self,
        prompt: str,
        model_name: str = "local",
        max_tokens: int = 1000,
    ) -> Tuple[str, int, float]:
        """
        Call local model (simulated for now).
        
        In production, this would call Ollama, LM Studio, or similar.
        """
        start_time = time.time()
        
        # Simulated response for local model
        response_text = f"[Local Model {model_name}] Analyzed prompt and generated reasoning..."
        tokens = len(prompt.split()) + len(response_text.split())
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Local model call completed: {tokens} tokens, {latency_ms:.2f}ms")
        return response_text, tokens, latency_ms

    async def generate_reasoning(
        self,
        application_data: Dict[str, Any],
        model: str = settings.openai_model,
        include_metrics: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate LLM reasoning for an application.
        
        Returns:
            (reasoning_text, metadata)
        """
        # Build context string
        context = self._build_context(application_data)
        
        prompt = f"""You are an expert credit underwriter. Analyze the following application and provide 
a thorough risk assessment with key concerns and recommendations.

APPLICATION DETAILS:
{context}

Provide:
1. Overall risk assessment (Low/Medium/High)
2. Key concerns or red flags
3. Positive indicators
4. Recommendation with justification
5. Suggested approval conditions if applicable

Be concise but thorough."""

        try:
            if model == settings.openai_model or model == settings.openai_model_fast:
                text, tokens, latency = await self.call_openai(
                    prompt, 
                    model=model,
                    max_tokens=1000
                )
            elif model == settings.gemini_model:
                text, tokens, latency = await self.call_gemini(
                    prompt,
                    max_tokens=1000
                )
            else:
                text, tokens, latency = await self.call_local_model(prompt)
            
            metadata = {
                "model": model,
                "tokens_used": tokens,
                "latency_ms": latency,
                "success": True,
            }
            
            if include_metrics:
                metadata["cost_estimate"] = self._estimate_cost(model, tokens)
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return "", {"success": False, "error": str(e)}

    def _build_context(self, data: Dict[str, Any]) -> str:
        """Build context string from application data."""
        context_parts = []
        
        # Personal info
        context_parts.append(f"Name: {data.get('full_name', 'N/A')}")
        context_parts.append(f"Age: ~{self._calculate_age(data.get('date_of_birth', ''))}")
        
        # Financial
        annual_income = data.get('annual_income', 0)
        monthly_income = annual_income / 12
        context_parts.append(f"Annual Income: ${annual_income:,.0f}")
        context_parts.append(f"Monthly Income: ${monthly_income:,.0f}")
        context_parts.append(f"Monthly Expenses: ${data.get('monthly_expenses', 0):,.0f}")
        
        # Employment
        context_parts.append(f"Employment: {data.get('employment_status', 'N/A')} at {data.get('employer', 'N/A')}")
        context_parts.append(f"Years Employed: {data.get('years_employed', 0)}")
        
        # Credit
        context_parts.append(f"Credit Score: {data.get('credit_score', 0)}")
        context_parts.append(f"Existing Debts: ${data.get('existing_debts', 0):,.0f}")
        context_parts.append(f"Active Accounts: {data.get('number_of_accounts', 0)}")
        context_parts.append(f"Delinquencies: {data.get('delinquencies', 0)}")
        
        # Loan Request
        loan_amount = data.get('loan_amount', 0)
        context_parts.append(f"Loan Request: ${loan_amount:,.0f}")
        context_parts.append(f"Term: {data.get('loan_term_months', 0)} months")
        context_parts.append(f"Purpose: {data.get('loan_purpose', 'N/A')}")
        
        # Notes
        if data.get('applicant_notes'):
            context_parts.append(f"Additional Notes: {data.get('applicant_notes')}")
        
        return "\n".join(context_parts)

    @staticmethod
    def _calculate_age(dob: str) -> int:
        """Rough age calculation from DOB string (YYYY-MM-DD)."""
        if not dob:
            return 0
        try:
            from datetime import datetime
            birth_date = datetime.strptime(dob, "%Y-%m-%d")
            today = datetime.today()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except:
            return 0

    @staticmethod
    def _estimate_cost(model: str, tokens: int) -> float:
        """Estimate API cost based on model and token count."""
        # Approximate pricing per 1K tokens
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
        }
        
        # Assume output is roughly 40% of input
        if model in pricing:
            rate = (pricing[model]["input"] * 0.6 + pricing[model]["output"] * 0.4) / 1000
            return tokens * rate
        
        return 0.0
