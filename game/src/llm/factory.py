from llm.instructor import InstructorLLM

class LLMFactory:

    @classmethod
    def create(cls):
        return InstructorLLM()

