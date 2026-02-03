import os
from openai import OpenAI
from logger_setup import logger
from utils.text import sanitize_output_text
from llm.tool_manager import ToolManager, ToolDefinition, ToolCall

class InstructorLLM:
    def __init__(self):
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.history = []
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables.")
        
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key or "missing_key"
        )
        self.tool_manager = ToolManager()

    def reset(self, session):
        self.history = []

    def system(self, system_instruction: str):
        if system_instruction:
            self.history.append({"role": "system", "content": system_instruction})

    def chat(self, session, user_input: str) -> dict:
        if not user_input:
            return {"text": "No input provided.", "expressions": [], "action": None}
        self._trim_history()
        self._add_to_history("user", user_input)

        # 1. Update available tools based on current state
        possible_action_ids = session.state_engine.get_possible_action_ids()
        tools = []
        for action_id in possible_action_ids:
            name = session.state_engine.get_action_name(action_id)
            description = session.state_engine.get_action_description(action_id)
            tools.append(ToolDefinition(name=name, description=description))
        
        self.tool_manager.set_tools(tools)

        # 2. Build the System Prompt
        combined_history = [
            {"role": "system", "content": session.state_engine.get_global_system_prompt()},
            {"role": "system", "content": session.state_engine.get_state_system_prompt()},
            {"role": "system", "content": self.tool_manager.get_tool_instructions()},
        ] + self.history

        # Debug logging
        # for entry in combined_history:
        #     logger.debug(f"{entry['role']}: {entry['content'][:100]}...")

        # 3. Call LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=combined_history,
                temperature=0.1,
                max_tokens=2000
            )
            raw_content = response.choices[0].message.content
            
            if raw_content is None:
                logger.warning("LLM returned None content.")
                return {"text": "Ich bin sprachlos...", "action": None}

            self._add_to_history(role="assistant", message=raw_content)

            # 4. Parse Response using ToolManager
            result = self.tool_manager.parse_response(raw_content)

            if isinstance(result, ToolCall):
                return {"text": sanitize_output_text(result.execution_text), "action": result.tool_name}
            elif result == "HELP_REQUESTED":
                 # Fallback logic for help generation could go here
                 hint = self._generate_hint(session)
                 return {"text": sanitize_output_text(hint), "action": None}
            elif isinstance(result, str):
                return {"text": sanitize_output_text(result), "action": None}
            else:
                return {"text": sanitize_output_text(raw_content), "action": None}

        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return {"text": "Ich habe Kopfschmerzen...", "action": None}

    def _add_to_history(self, role, message):
        if not message:
            return
        
        if self.history and self.history[-1]["role"] == role and self.history[-1]["content"] == message:
            return
        
        self.history.append({"role": role, "content": message})

    def _trim_history(self):
        entry_limit = 8
        self.history = self.history[-entry_limit:]

    def _generate_hint(self, session) -> str:
        """Generates a hint for the user."""
        current_actions_with_desc = {
            session.state_engine.get_action_name(action): session.state_engine.get_action_description(action)
            for action in session.state_engine.get_possible_action_ids()
        }
        descriptions_text = ", ".join(current_actions_with_desc.values())
        hint_prompt = f"Du bist ein mürrischer Haudegen. Der Spieler hat um Hilfe gebeten. Schlage ihm 2-3 interessante Dinge vor, basierend auf: {descriptions_text}. Fass dich kurz und bleib im Charakter."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": hint_prompt}]
            )
            return response.choices[0].message.content
        except Exception:
            return "Versuch mal was anderes."
