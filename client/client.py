from abc import ABC, abstractmethod, abstractproperty

class Client(ABC):
    @abstractmethod
    def login(self, username, password):
        pass

    @abstractmethod
    def update(self):
    	pass

    @abstractproperty
    def id(self):
        pass
