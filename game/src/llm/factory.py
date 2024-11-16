from llm.openai import OpenAILLM
#from llm.gemini import GeminiLLM
#from llm.ollama import OllamaLLM

class LLMFactory:

    @classmethod
    def create(cls):

        return OpenAILLM()
        #return GeminiLLM()
        #return OllamaLLM()

