class Game:

    def __init__(self, giocatore1, giocatore2):
        self.giocatore1 = giocatore1
        self.giocatore2 = giocatore2
        self.punteggio1 = 0
        self.punteggio2 = 0

        #STATO = 0 -> INVIO FOTO INIZIALE
        #STATO = 1 -> INVIO FOTO GIOCO
        #STATO = 2 -> INVIO AUDIO
        self.stato_g1 = 0
        self.stato_g2 = 0
        self.data_g1 = None
        self.data_g2 = None

