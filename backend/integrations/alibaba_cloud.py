"""
AutoMaintainer - Alibaba Cloud Integration Module
Demonstrates integration with Alibaba Cloud services for the Qwen Cloud Hackathon
"""

import os
import httpx
from typing import Dict, Any, Optional
import json


class AlibabaDashScopeAPI:
    """
    Alibaba Cloud DashScope API Integration for Qwen LLM Models
    
    This module demonstrates how AutoMaintainer leverages Alibaba Cloud's
    enterprise-grade LLM APIs for multi-agent orchestration.
    
    Free Tier: 70+ million tokens per account
    Documentation: https://help.aliyun.com/document_detail/611472.html
    API Endpoint: https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
    """
    
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.model = os.getenv("QWEN_MODEL", "qwen-plus")
        
        if not self.api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY not set. Get it from: https://alibabacloud.com/free"
            )
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate text using Alibaba Cloud Qwen API
        
        Args:
            prompt: User message/prompt
            system_prompt: System instructions for the agent
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0.0-2.0)
        
        Returns:
            Response containing generated text and usage info
        
        Usage:
            client = AlibabaDashScopeAPI()
            result = await client.generate_text(
                prompt="Analyze this GitHub issue...",
                system_prompt="You are a code analyzer."
            )
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt or "You are an AI assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(
                        f"Alibaba Cloud API error: {response.status_code} - {response.text}"
                    )
                
                return response.json()
        
        except httpx.TimeoutException:
            raise Exception("Alibaba Cloud API request timed out")
        except Exception as e:
            raise Exception(f"Alibaba Cloud API call failed: {str(e)}")
    
    async def generate_code(
        self,
        requirement: str,
        language: str = "python"
    ) -> str:
        """Generate code using Qwen's code generation capability"""
        
        system = f"You are an expert {language} developer. Generate production-ready code."
        prompt = f"Implement: {requirement}"
        
        result = await self.generate_text(prompt, system, max_tokens=4000)
        return result["output"]["text"]


class AlibabaCosts:
    """
    Cost tracking for Alibaba Cloud services
    Demonstrates free tier usage and helps track when free credits deplete
    """
    
    FREE_TIER = {
        "qwen_tokens": 70_000_000,  # 70M free tokens
        "ecs_credits": 90,  # $90 USD
        "ecs_duration_months": 3,
        "rds_trial_days": 30,
        "bandwidth_gb_per_month": 100,  # Generous free allowance
    }
    
    PRICING = {
        "qwen_plus_per_1m_tokens": 0.08,  # USD
        "qwen_turbo_per_1m_tokens": 0.04,  # USD
        "qwen_long_per_1m_tokens": 0.20,  # USD
        "ecs_2core_4gb_per_hour": 0.04,  # Approximate after free tier
        "rds_mysql_per_day": 0.15,  # Approximate after free tier
        "bandwidth_per_gb": 0.12,  # After free allowance
    }
    
    @staticmethod
    def estimate_monthly_cost(
        monthly_api_calls: int = 1000,
        tokens_per_call: int = 2000,
        model: str = "qwen-plus",
        ecs_hours_per_month: int = 730,
        include_database: bool = False
    ) -> Dict[str, float]:
        """
        Estimate monthly Alibaba Cloud costs after free tier
        
        Args:
            monthly_api_calls: Number of LLM API calls per month
            tokens_per_call: Average tokens per API call
            model: qwen-plus, qwen-turbo, or qwen-long
            ecs_hours_per_month: Hours to run ECS instance
            include_database: Include RDS database costs
        
        Returns:
            Cost breakdown by service
        """
        
        total_tokens = monthly_api_calls * tokens_per_call
        
        costs = {
            "llm_api_cost": 0,
            "ecs_cost": 0,
            "database_cost": 0,
            "bandwidth_cost": 0,
            "total_monthly": 0,
        }
        
        # LLM API costs (if exceeds free 70M tokens)
        if total_tokens > AlibabaCosts.FREE_TIER["qwen_tokens"]:
            excess_tokens = total_tokens - AlibabaCosts.FREE_TIER["qwen_tokens"]
            cost_per_token = AlibabaCosts.PRICING[f"{model}_per_1m_tokens"] / 1_000_000
            costs["llm_api_cost"] = excess_tokens * cost_per_token
        
        # ECS costs (if exceeds 3-month $90 free credit)
        monthly_ecs = ecs_hours_per_month * AlibabaCosts.PRICING["ecs_2core_4gb_per_hour"]
        # Assume $90 / 3 months = $30 per month free
        if monthly_ecs > 30:
            costs["ecs_cost"] = monthly_ecs - 30
        
        # Database costs (if exceeds 30-day trial)
        if include_database:
            costs["database_cost"] = AlibabaCosts.PRICING["rds_mysql_per_day"] * 30
        
        # Bandwidth (generous free allowance)
        costs["bandwidth_cost"] = 0  # Assuming under 100GB/month
        
        costs["total_monthly"] = sum(c for k, c in costs.items() if k != "total_monthly")
        
        return costs


class AlibabaDashboardMetrics:
    """
    Helper for tracking Alibaba Cloud service usage
    """
    
    @staticmethod
    def generate_deployment_info() -> str:
        """Generate deployment info for Devpost submission"""
        
        info = {
            "cloud_provider": "Alibaba Cloud",
            "primary_service": "Model Studio (Qwen LLM API)",
            "compute_service": "Elastic Compute Service (ECS)",
            "database_service": "ApsaraDB RDS for MySQL",
            "api_endpoint": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            "free_tier": {
                "ai_tokens": "70+ million",
                "duration": "Perpetual free tier",
                "compute_credits": "$90 (3 months)",
                "database_trial": "1 month free",
            },
            "estimated_cost_with_free_tier": "$0 for 3 months",
            "deployment_guide": "See ALIBABA_DEPLOYMENT.md in repository root",
            "qwen_models_available": [
                "qwen-plus (highest quality, $0.08/1M tokens)",
                "qwen-turbo (fast & efficient, $0.04/1M tokens)",
                "qwen-long (context window, $0.20/1M tokens)"
            ]
        }
        
        return json.dumps(info, indent=2)


# Example usage demonstrating Alibaba Cloud integration
async def example_workflow():
    """
    Example: How AutoMaintainer uses Alibaba Cloud
    """
    
    # Initialize Alibaba Cloud API client
    api = AlibabaDashScopeAPI()
    
    # Example 1: Issue Analysis Agent
    issue_analysis_prompt = """
    Analyze this GitHub issue:
    "Add support for async database queries in ORM"
    
    Provide:
    1. Issue severity (critical/high/medium/low)
    2. Root cause analysis
    3. Recommended solution
    """
    
    system = "You are an issue analysis expert."
    
    # This would be awaited in actual usage
    # result = await api.generate_text(issue_analysis_prompt, system)
    
    # Example 2: Cost tracking
    costs = AlibabaCosts.estimate_monthly_cost(
        monthly_api_calls=500,
        tokens_per_call=2000,
        model="qwen-plus",
        ecs_hours_per_month=730,
        include_database=True
    )
    
    print("Estimated Monthly Costs (after free tier):")
    print(f"  LLM API: ${costs['llm_api_cost']:.2f}")
    print(f"  ECS: ${costs['ecs_cost']:.2f}")
    print(f"  Database: ${costs['database_cost']:.2f}")
    print(f"  Total: ${costs['total_monthly']:.2f}")
    
    # Example 3: Deployment info
    print("\nAlibaba Cloud Deployment Info:")
    print(AlibabaDashboardMetrics.generate_deployment_info())


if __name__ == "__main__":
    # Print deployment info
    print(AlibabaDashboardMetrics.generate_deployment_info())
