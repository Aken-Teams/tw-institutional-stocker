# -*- coding: utf-8 -*-
"""Base AI analysis module with OpenAI integration."""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class AIAnalysisBase:
    """Base class for AI analysis with OpenAI integration."""
    
    def __init__(self):
        self.client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.language = os.getenv("AI_ANALYSIS_LANGUAGE", "zh-TW")
        self.enabled = os.getenv("ENABLE_AI_ANALYSIS", "true").lower() == "true"
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if self.enabled:
            self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.error("OPENAI_API_KEY not found in environment variables")
            self.enabled = False
            return
            
        if api_key == "your_openai_api_key_here":
            self.logger.error("Please set your actual OpenAI API key in .env file")
            self.enabled = False
            return
            
        try:
            self.client = OpenAI(api_key=api_key)
            self.logger.info("OpenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            self.enabled = False
    
    def _call_openai(self, messages: List[Dict[str, str]], system_prompt: str = None) -> Optional[str]:
        """Make a call to OpenAI API."""
        if not self.enabled or not self.client:
            self.logger.warning("AI analysis is disabled")
            return None
        
        try:
            if system_prompt:
                messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {e}")
            return None
    
    def _format_number(self, num: float, decimal_places: int = 2) -> str:
        """Format number for display."""
        if abs(num) >= 1_000_000:
            return f"{num/1_000_000:.{decimal_places}f}M"
        elif abs(num) >= 1_000:
            return f"{num/1_000:.{decimal_places}f}K"
        else:
            return f"{num:.{decimal_places}f}"
    
    def _format_percentage(self, num: float, decimal_places: int = 2) -> str:
        """Format percentage for display."""
        return f"{num:.{decimal_places}f}%"
    
    def _load_json_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load JSON data from file."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"File not found: {file_path}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to load JSON from {file_path}: {e}")
            return None
    
    def _save_analysis_result(self, data: Dict[str, Any], file_path: str) -> bool:
        """Save analysis result to JSON file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Analysis result saved to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save analysis result to {file_path}: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if AI analysis is enabled."""
        return self.enabled