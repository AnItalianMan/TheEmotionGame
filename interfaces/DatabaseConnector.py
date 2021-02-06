from abc import ABCMeta, abstractmethod


class DatabaseConnector:
    __metaclass__ = ABCMeta

    @abstractmethod
    def connect(self):
        raise NotImplementedError

    @abstractmethod
    def top(self):
        raise NotImplementedError