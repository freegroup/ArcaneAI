from abc import ABC, abstractmethod

class BaseJukebox(ABC):

    @abstractmethod
    def play_sound(self, session, file_name, volume=100, loop=True, duration=2):
        pass

    @abstractmethod
    def stop_all(self, session):
        pass


    @abstractmethod
    def stop_ambient(self, session):
        pass

