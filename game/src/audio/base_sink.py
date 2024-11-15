from abc import ABC, abstractmethod


class BaseAudioSink(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def write(self, session, chunk):
        pass

    @abstractmethod
    def close(self, session):
        pass
