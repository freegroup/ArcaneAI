import openai
from openai import OpenAI
import json
import sys

import tiktoken
import os
from logger_setup import logger

from llm.base import BaseLLM

def make_serializable(obj):
    """Convert an object to a form that is JSON serializable."""
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    elif hasattr(obj, '__dict__'):
        return make_serializable(vars(obj))
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)


# Definition der Klasse OpenAILLM, die von BaseLLM erbt
class OpenAILLM(BaseLLM):
    def __init__(self):
        super().__init__()
        #self.model = "gpt-4"
        #self.model = "gpt-3.5-turbo"
        #self.model = "gpt-4o-mini"
        self.model = "gpt-4o"
  
        self.history = []
        self.max_tokens = 2048
        self.stop = None
        self.frequency_penalty = 0
        self.presence_penalty = 0
        self.temperature = 0.1
        self.top_p = 0.95
        self.token_limit = 4000 
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.fatal("API key for OpenAI not found in environment variables.")
            sys.exit(1)
     
        self.client = OpenAI(api_key=self.api_key)


    def dump(self):
        logger.info(json.dumps(self.history, indent=4))


    def reset(self, session):
        self.history = []


    def system(self, system_instruction):
        if system_instruction:
            self._add_to_history("system", system_instruction)
        else:
            logger.warning("No system instruction provided.")


    def chat(self, session, user_input):
        if not user_input:
            return {"text": "No input provided.", "expressions": [], "action": None}
        self._trim_history()
        self._add_to_history("user", user_input)

        response = self._call_openai_model(session, self.history)
        if (response["text"] is None or response["text"].strip() == "") and response["action"]:
            response = self._response_for_action(session, response)
        
        # strip off crap repeated phrases
        # I didn't manage this by using a good system prompt.
        response["text"] =  response["text"].split("Was möchtest du ")[0]
        response["text"] =  response["text"].split("Was sollen wir")[0]

        self._add_to_history("assistant", response["text"])
        return response
    

    def _add_to_history(self, role, message):
        if not message:
            logger.warning("No message provided.")
            return
        
        if self.history and self.history[-1]["role"] == role and self.history[-1]["content"] == message:
            logger.error("Duplicate message detected; not adding to history.")
            return
        
        self.history.append({"role": role, "content": message})


    def _call_openai_model(self, session, history):
        combined_history = [
            {"role": "system", "content": session.state_engine.get_global_system_prompt()},
            {"role": "system", "content": session.state_engine.get_state_system_prompt()},
            {"role": "system", "content": self._possible_actions_instruction(session)},
        ] + history

        functions = self._define_action_functions(session)
        logger.debug(json.dumps([ func["name"] for func in functions], indent=4))

        try:
            logger.debug(json.dumps(combined_history, indent=4))

            response = self.client.chat.completions.create(
                model=self.model,
                messages=combined_history,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                functions=functions if len(functions)>0 else None,
            )
            return self._process_response(response)
        except openai.OpenAIError as e:
            logger.error(f"Error: {e}")
            return {"text": "I'm sorry, there was an issue processing your request.", "expressions": [], "action": None}


    def _define_action_functions(self, session):
        return [
            {
                "name": session.state_engine.get_action_name(action),
                "description": session.state_engine.get_action_description(action),
                "parameters": {}  # No parameters
            }
            for action in session.state_engine.get_possible_action_ids()
        ]

    def _possible_actions_instruction(self, session):
        possible_actions = session.state_engine.get_possible_action_names()
        possible_actions_str = ', '.join(f"'{action}'" for action in possible_actions)
        return f"Benutze diese bereitgestellen Funktionen oder Tols um dem Benutzer zu helfen: [{possible_actions_str}]"


    def _process_response(self, response):
        text, action = "", None
        if response and response.choices:
            choice = response.choices[0].message
            if choice.function_call:
                action = choice.function_call.name
            elif choice.content:
                text = choice.content
        return {"text": text, "expressions":[], "action": action}


    def _response_for_action(self, session, initial_response):
        action_name = initial_response["action"]
        history = self.history.copy()
        if action_name in session.state_engine.get_possible_action_names():
            action_id = session.state_engine.get_action_id(action_name)
            # temp. add this to the history. but we do not want pollute the history with 
            # That kind of instructions
            history.append({"role": "system", "content": session.state_engine.get_action_system_prompt(action_id)})
            history.append({"role": "system", "content": f"""
                Respond as if the action '{action_name}' was executed successfully. 
                Do not reveal any internal details to the user.
            """})
        else:
            # If the action is not valid, we clear it to avoid returning an incorrect action
            action_name = None

        # Retry without requesting a function call, focusing on obtaining a text response
        second_response = self._call_openai_model(session, history)

        # Preserve the original action and update only the text
        initial_response["text"] = second_response["text"]
        initial_response["action"] = action_name  # Ensure the action from the first response is kept

        return initial_response


    def _trim_history(self):
        entry_limit = 8
        self.history = self.history[-entry_limit:]

        #while self._count_tokens(self.history) > self.token_limit:
        #    if len(self.history) > 1:
        #        self.history.pop(0)
        #    else:
        #        break


    def _count_tokens(self, messages):
        return sum(len(self.tokenizer.encode(message["content"])) for message in messages)