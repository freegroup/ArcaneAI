import os
import time
import json
import re

import google.generativeai as genai
from logger_setup import logger

from llm.base import BaseLLM

# Definition der Klasse OpenAILLM, die von BaseLLM erbt
class GeminiLLM(BaseLLM):
    def __init__(self):
        super().__init__()
        self.max_tokens= 8192
        self.history = []
        #self.model_name = "gemini-1.5-flash"      # latest
        self.model_name = "gemini-1.5-pro"  # stable
        self.generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,  # 64
            "max_output_tokens": 210, #self.max_tokens,
            "response_mime_type": "text/plain",
        }
        self.api_key=os.environ["GEMINI_API_KEY"]
        if not self.api_key:
            raise ValueError("API key 'GEMINI_API_KEY' not found in environment variables.")
        genai.configure(api_key=self.api_key)
        self.model_info = genai.get_model(f"models/{self.model_name}")

        # just for token count....not for Q&A or anything else
        self.token_model = genai.GenerativeModel(f"models/{self.model_name}")

        # Returns the "context window" for the model,
        # which is the combined input and output token limits.
        logger.info(f"Gemini {self.model_info.input_token_limit=}")
        logger.info(f"Gemini {self.model_info.output_token_limit=}")


    def dump(self):
        logger.info(json.dumps(self.history, indent=4))


    def reset(self, session):
        self.history = []


    def system(self, system_instruction):
        if system_instruction:
            self._add_to_history(role="model", message=system_instruction.replace(f'\n', ''))

    def chat(self, session, user_input):
        if not user_input:
            logger.error("Error: No user input provided.")
            return {"text": "No input provided.", "expressions": [], "action": None}

        user_input = user_input.replace(f'\n', '')
        tools = [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name=session.state_engine.get_action_name(action_id),
                        description=session.state_engine.get_action_description(action_id),
                        parameters=None
                    )
                ]
            )
            for action_id in session.state_engine.get_possible_action_ids()
        ]

        possible_actions_instruction = re.sub(r"\s+", " ", f"""
            Im Hintergrund wähle ich je nach Gesprächskontext oder auf expliziten Wunsch des Benutzers die 
            passende Funktion aus. Dabei achte ich darauf, dass das Handlungsverb der Aktion semantisch 
            zur Anweisung passt, um Verwechslungen wie „öffne...“ statt „untersuche...“. Verben die semantisch identisch
            sind wie gehen, laufen, rennen oder aufheben, nehmen,...können als identisch und gleichwertig angesehen werden.
            Jede gewählte Aktion soll im Sinne der Absicht des Nutzers ausgeführt werden.

            Wenn keine dieser Funktionen dem Befehl des Nutzers entspricht, fahre ich ohne technische 
            Hinweise oder Rückmeldung ganz normal im Gesprächsverlauf fort, ohne eine Aktion auszuführen.
            Achte drauf dem Benutzer IMMER einen text als zu liefern.
        """)
        self._trim_history_to_fit(user_input)
  
        # Erster Modellaufruf mit "function_calling_config" auf "ANY" um zu versuchen "action" und "text" zu bekommen
        #
        result = self._get_response_with_config(session, 
                                                user_input, 
                                                tools, 
                                                possible_actions_instruction, 
                                                function_calling_config="AUTO")
        action = result["action"]

        # Falls Gemini nur "action" geliefert hat, dann starten wir einen zweiten Aufruf um uns nur eine "text" Antwort abzuholen.
        # Kann manchmal passieren. AI = fuzzy
        #
        if result["text"] is None:
            logger.debug("No text response; retrying with function_calling_config set to 'NONE'.")
            if action in session.state_engine.get_possible_action_names():
                self.system(re.sub(r"\s+", " ",f""" (Hinweis: Antworte so, als ob die Aktion '{result["action"]}' erfolgreich ausgeführt wurde.
                    Achte bitte darauf, dass du so Antwortest, als ob die Aktion erfolgreich war und du 
                    diese ausgeführt hast. Egal welche anderen Annahmen du triffst. Diese information NIEMALS 
                    dem Benutzer zeigen oder zurückliefern) 
                    """))
            else:
                result["action"] = None

            second_result = self._get_response_with_config(session, user_input, tools, possible_actions_instruction, function_calling_config="NONE")

            # Merging der Antworten
            result["text"] = second_result["text"] if result["text"] is None else result["text"]

            # remove the fucking Gemini prompt append....
            text = result["text"]
            result["text"] = text[:text.find("(Hinweis:")] if "(Hinweis:" in text else text

            if result["action"] is None and second_result["action"] is not None:
                result["action"] = second_result["action"]

        # Append user input to history
        self._add_to_history(role='user', message=user_input)
        self._add_to_history(role='model', message=result["text"] )

        logger.debug(json.dumps(result, indent=4))
        return result


    def _add_to_history(self, role, message):
        if not message:
            logger.warning("No message provided.")
            return
        
        # Check if history is empty or the last entry is different in content
        if self.history and self.history[-1]["role"] == role:
            # If the message is identical to the last entry, skip adding
            if message in self.history[-1]["parts"]:
                logger.error("Duplicate message detected; not adding to history.")
                return
            
            # If the role matches the last entry, append the message to `parts`
            self.history[-1]["parts"].append(message)
        else:
            # Add a new entry if role is different or history is empty
            self.history.append({"role": role, "parts": [message]})


    def _get_response_with_config(self, session, user_input, tools, instruction, function_calling_config):
        max_retries = 2
        attempt = 0
        
        while attempt <= max_retries:
            try:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=self.generation_config,
                    system_instruction=f"{session.state_engine.get_global_system_prompt()}. {instruction}",
                    tools=tools,
                    safety_settings={
                        'HATE': 'BLOCK_NONE',
                        'HARASSMENT': 'BLOCK_NONE',
                        'SEXUAL': 'BLOCK_NONE',
                        'DANGEROUS': 'BLOCK_NONE'
                    },
                    tool_config={'function_calling_config': function_calling_config},
                )

                chat_session = model.start_chat(
                    history=self.history,
                    enable_automatic_function_calling=False
                )

                response = chat_session.send_message(user_input)
                result = {"text": None, "expressions": [], "action": None}

                # Process response parts
                for part in response.parts:
                    if part.text and not result["text"]:
                        result["text"] = part.text
                    if part.function_call and not result["action"]:
                        result["action"] = part.function_call.name

                return result  # Exit the loop and function if successful

            except Exception as e:
                logger.error(e)
                logger.error(json.dumps(self.history, indent=4))
                attempt += 1
                if attempt > max_retries:
                    logger.error("Max retries reached. Returning empty result.")
                    return {"text": "Error: Unable to get response after multiple attempts.", "expressions": [], "action": None}
                time.sleep(0.1)


    def _trim_history_to_fit(self, user_input):
        """Trim history to fit within token limit when adding user input."""
        # Calculate tokens needed for user_input
        input_tokens = self._calculate_token_count(user_input)
        
        # Calculate current history token count
        history_tokens = sum(self._calculate_token_count(entry["parts"][0]) for entry in self.history)
        
        # Trim history if total tokens exceed max allowed tokens
        while history_tokens + input_tokens > self.max_tokens and self.history:
            # Remove oldest entry
            removed_entry = self.history.pop(0)
            history_tokens -= self._calculate_token_count(removed_entry["parts"][0])


    def _calculate_token_count(self, text):
        """Calculate token count for a given text using the Gemini API."""
        return self.token_model.count_tokens(text).total_tokens

