from abc import abstractmethod, ABC

# Step 1: Define the Base Class using abc
class Base(ABC):

    @abstractmethod
    def stop(self, session):
        pass

    @abstractmethod
    def set(self, session, expressions, inventory):
        """Sets the expression to use"""
        pass
