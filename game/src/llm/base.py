import abc

# Definition of BaseLLM class 
class BaseLLM(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def chat(self, user_input):
        pass

    @abc.abstractmethod
    def system(self, system_instruction):
        pass


    @abc.abstractmethod
    def dump(self):
        pass


    @abc.abstractmethod
    def reset(self, session):
        pass
