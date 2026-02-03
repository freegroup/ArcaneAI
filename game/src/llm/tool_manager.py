from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
import json
import re
from logger_setup import logger
from utils.text import extract_json_text_from_raw_text

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None

class ToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    execution_text: Optional[str] = None

class ToolManager:
    """
    Manages the integration of tools with LLMs. 
    Handles formatting of tool definitions for prompts and parsing of tool calls from responses.
    """
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}

    def set_tools(self, tools: List[ToolDefinition]):
        self.tools = {t.name: t for t in tools}

    def get_tool_instructions(self) -> str:
        """
        Returns the system prompt instructions for using the available tools.
        Currently uses a JSON-based approach compatible with most instruction-tuned models.
        """
        if not self.tools:
            return ""

        tools_desc = []
        for tool in self.tools.values():
            tools_desc.append(f"- {tool.name}: {tool.description}")
        
        tools_str = "\n".join(tools_desc)

        return f"""
AVAILABLE TOOLS:
{tools_str}

INSTRUCTIONS:
You can use the above tools to perform actions. To use a tool, you MUST respond with a JSON object.
Do NOT output any other text before or after the JSON.

FORMAT:
{{
    "decision_type": "tool_use",
    "tool_name": "<name_of_tool>",
    "parameters": {{ <optional_parameters> }},
    "execution_text": "<narrative_description_of_action>"
}}

If you do not want to use a tool, respond with a conversation object:
{{
    "decision_type": "conversation",
    "content": "<your_response_text>"
}}

IMPORTANT OUTPUT RULES:
1. Do NOT use any Markdown formatting (no bold **, no italics *, no lists, no headers).
2. Do NOT use Emojis.
3. Keep the output plain text only.
4. The output is used for Text-to-Speech, so write naturally spoken text.

If the user asks for help or options, respond with:
{{
    "decision_type": "help"
}}
"""

    def parse_response(self, response_text: str) -> Union[ToolCall, str, None]:
        """
        Parses the LLM response.
        Returns:
        - ToolCall object if a valid tool was called.
        - str if it's a conversation response.
        - None if parsing failed or 'help' was requested.
        """
        json_str = extract_json_text_from_raw_text(response_text)
        
        if not json_str:
            # Fallback: If no JSON found, treat as conversation if it looks like text
            if response_text.strip():
                logger.warning("No JSON found in response, treating as conversation.")
                return response_text
            return None

        try:
            data = json.loads(json_str)
            decision_type = data.get("decision_type")

            if decision_type == "tool_use":
                tool_name = data.get("tool_name")
                if tool_name in self.tools:
                    return ToolCall(
                        tool_name=tool_name,
                        parameters=data.get("parameters", {}),
                        execution_text=data.get("execution_text", "")
                    )
                else:
                    logger.warning(f"LLM tried to use unknown tool: {tool_name}")
                    return None # Or return an error message to the LLM?

            elif decision_type == "conversation":
                return data.get("content", "")
            
            elif decision_type == "help":
                return "HELP_REQUESTED"

            elif decision_type == "action": # Backward compatibility for old prompt style if needed
                 tool_name = data.get("name")
                 if tool_name in self.tools:
                    return ToolCall(
                        tool_name=tool_name,
                        parameters={},
                        execution_text=data.get("execution_text", "")
                    )
                 return None

            else:
                logger.warning(f"Unknown decision_type: {decision_type}")
                return None

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from response.")
            return None
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return None
