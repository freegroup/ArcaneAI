from llm.openai import OpenAILLM
#from llm.gemini import GeminiLLM
from llm.ollama import OllamaLLM
from llm.deepseek import DeepSeekLLM
from llm.instructor import InstructorLLM

class LLMFactory:

    @classmethod
    def create(cls):
        return InstructorLLM()
        #return OpenAILLM()
        #return GeminiLLM()
        #return OllamaLLM()
        #return DeepSeekLLM()

