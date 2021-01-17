from Giocatore import Giocatore


class Game:

    def __init__(self, giocatore1_chatid, giocatore2_chatid):
        self.giocatore1 = Giocatore(giocatore1_chatid)
        self.giocatore2 = Giocatore(giocatore2_chatid)
        self.foto = None
