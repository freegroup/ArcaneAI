"""
SAP AI Core LLM Provider using Orchestration Service.
"""
import os
from typing import List
from gen_ai_hub.orchestration.service import OrchestrationService, OrchestrationConfig
from gen_ai_hub.orchestration.models.llm import LLM
from gen_ai_hub.orchestration.models.message import Message
from gen_ai_hub.orchestration.models.template import Template, TemplateValue
from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse


class SAPAICoreProvider(BaseLLMProvider):
    """SAP AI Core provider using Orchestration Service."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str,
        auth_url: str,
        resource_group: str = "default",
        model: str = "gpt-4o",
        deployment_id: str = None,
        temperature: float = 0.1,
        max_tokens: int = 2000
    ):
        """Initialize SAP AI Core provider."""
        # Set environment variables for SDK
        os.environ['AICORE_CLIENT_ID'] = client_id
        os.environ['AICORE_CLIENT_SECRET'] = client_secret
        os.environ['AICORE_BASE_URL'] = base_url
        os.environ['AICORE_AUTH_URL'] = auth_url
        os.environ['AICORE_RESOURCE_GROUP'] = resource_group
        
        # Create LLM config and store it
        self.llm_config = LLM(name=model, parameters={"max_tokens": max_tokens, "temperature": temperature})
        
        # Create orchestration service (uses env vars automatically)
        # Pass deployment_id if provided (for orchestration service deployment)
        self.service = OrchestrationService(deployment_id=deployment_id)
        
        super().__init__(api_key="", model=model, temperature=temperature, max_tokens=max_tokens)
    
    def _validate_config(self):
        """Validate configuration."""
        if not os.environ.get('AICORE_CLIENT_ID'):
            raise ValueError("SAP AI Core client_id is required")
    
    def chat(self, messages: List[LLMMessage]) -> LLMResponse:
        """Send chat completion request."""
        # Find the first system message to use as template
        system_message_index = next((i for i, msg in enumerate(messages) if msg.role == 'system'), -1)
        
        if system_message_index != -1:
            # Use the first system message for template
            system_message = messages[system_message_index]
            template_messages = [Message(role="system", content=system_message.content)]
            
            # All other messages go to history (excluding the one used for template)
            history_messages = messages[:system_message_index] + messages[system_message_index+1:]
        else:
            # No system message found, use default
            template_messages = [Message(role="system", content="You are a helpful AI assistant.")]
            history_messages = messages
            
        template = Template(messages=template_messages)
        
        # Create config for this request
        config = OrchestrationConfig(llm=self.llm_config, template=template)
        
        # Convert history messages to SDK format
        history = [Message(role=msg.role, content=msg.content) for msg in history_messages]
        
        try:
            # Call orchestration service
            response = self.service.run(config=config, history=history)
            
            # Extract content
            content = response.orchestration_result.choices[0].message.content
            
            return LLMResponse(content=content, model=self.model)
        except Exception as e:
            raise Exception(f"SAP AI Core error: {e}")
