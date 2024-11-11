from abc import ABC, abstractmethod

class BaseJukebox(ABC):

    @abstractmethod
    def play_sound(self, session, file_name, volume=100, loop=True):
        pass

    @abstractmethod
    def stop_all(self, session):
        pass

