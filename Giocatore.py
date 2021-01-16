class Giocatore:

    def __init__(self, chat_id):
        self.__chatid = chat_id
        self.punteggio = 0

        #STATO = 0 -> INVIO FOTO INIZIALE
        #STATO = 1 -> ATTESA
        #STATO = 2-> INVIO FOTO GIOCO
        #STATO = 3 -> INVIO AUDIO
        self.__stato = 0
        self.__data = None

    @property
    def chatid(self): return self.__chatid

    @chatid.setter
    def chatid(self, chatid: str): self.__chatid = chatid

    @property
    def stato(self): return self.__stato

    @stato.setter
    def stato(self, stato: str): self.__stato = stato

    @property
    def punteggio(self): return self.__punteggio

    @punteggio.setter
    def punteggio(self, punteggio: str): self.__punteggio = punteggio

    @property
    def data(self): return self.__data

    @data.setter
    def data(self, data: str): self.__data = data