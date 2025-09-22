import abc
from pydantic import BaseModel, Field
from typing import Literal, Union, Annotated

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


class Aktion(BaseModel):
    entscheidungstyp: Literal["aktion"]
    name: Literal[*VALID_ACTIONS]
    ausfuehrungstext: str = Field(..., description="Ein kurzer Satz im Charakter, der die Ausführung der Aktion bestätigt.")

class Konversation(BaseModel):
    entscheidungstyp: Literal["konversation"]
    inhalt: str

class HilfeAnfordern(BaseModel):
    entscheidungstyp: Literal["hilfe"]

class KombinierteAntwort(BaseModel):
    entscheidungstyp: Literal["kombiniert"]
    konversation: str
    biete_hilfe_an: bool

Entscheidung = Annotated[
    Union[Aktion, Konversation, HilfeAnfordern, KombinierteAntwort],
    Field(discriminator="entscheidungstyp")
]