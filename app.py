import json
import os
import subprocess
import traceback
from io import BytesIO
from PIL import Image
import requests
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from AzureBingService import AzureBingService
from AzureSpeechService import AzureSpeechService
from Game import Game
import random
from AzureVision import AzureVision
import yaml


class HandlerFunction:

    def __init__(self, name: str, callback):
        self.__name = name
        if callback is None:
            self.__callback = self.__default_callback
        else:
            self.__callback = callback

    @property
    def name(self): return self.__name

    @name.setter
    def name(self, name: str): self.__name = name

    @property
    def callback(self): return self.__callback

    @callback.setter
    def callback(self, callback):
        if callback is None: self.__callback = self.__default_callback
        self.__callback = callback

    def __default_callback(self, update, context):
        id = update.message.from_user['id']
        context.bot.send_message(chat_id=id, text='Callback is null')


class Bot:
    __emotion = ['rabbia', 'disprezzo', 'disgusto', 'paura', 'felice', 'neutro', 'tristezza', 'sorpreso']

    __dispatcher = None
    __botToken = ''

    __games = []
    __wait = []

    def __init__(self, botToken: str, azureSpeechToken: str, azureBingToken: str, azureVisionToken: str):
        self.__botToken = botToken
        self.__azureSpeechToken = azureSpeechToken
        self.__azureBingToken = azureBingToken
        self.__azureVisionToken = azureVisionToken
        self.__emotion_string = ""
        for emotion in self.__emotion:
            self.__emotion_string += emotion + ", "

        self.__emotion_string = self.__emotion_string[0:self.__emotion_string.__len__() - 2]

    def start_bot(self):
        updater = Updater(token=self.__botToken, use_context=True)
        #logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

        self.__dispatcher = updater.dispatcher
        # Aggiungo i comandi che iniziano con '/'
        command_list = []
        command_list.append(HandlerFunction('start', self.__start))
        command_list.append(HandlerFunction('stop', self.__stop))

        self.__register_function(command_list)

        unknown_handler = MessageHandler(Filters.command, self.__unknown)
        self.__dispatcher.add_handler(unknown_handler)

        audio_handler = MessageHandler(Filters.voice, self.__audio_handler)
        self.__dispatcher.add_handler(audio_handler)

        photo_handler = MessageHandler(Filters.photo, self.__photohandler)
        self.__dispatcher.add_handler(photo_handler)

        # Handler testuale
        text_handler = MessageHandler(Filters.text & (~Filters.command), self.__text_handler)
        self.__dispatcher.add_handler(text_handler)

        #PULSANTI
        button_handler = CallbackQueryHandler(self.__button_handler)
        self.__dispatcher.add_handler(button_handler)

        updater.start_polling()

    def in_game(self, chat_id):
        if chat_id in self.__wait:
            return True, "waiting", None

        for game in self.__games:
            if game.giocatore1.chatid == chat_id:
                return True, game, game.giocatore1
            elif game.giocatore2.chatid == chat_id:
                return True, game, game.giocatore2

        return False, "not in game", None

    def check_versus(self, game, bot):
        if game.giocatore1.stato == 1 and game.giocatore2.stato == 1:
            azure_vision = AzureVision(self.__azureVisionToken)
            operation = azure_vision.get_versus(BytesIO(game.giocatore1.data), BytesIO(game.giocatore2.data))
            if operation['status'] == "ok":
                game.foto = operation['image']
                bot.send_photo(game.giocatore1.chatid, photo=BytesIO(operation['image']))
                bot.send_photo(game.giocatore2.chatid, photo=BytesIO(operation['image']))

                # Lo stato del giocatore 1 resta ad uno perché deve inviare la foto
                game.giocatore1.stato = 0
                game.giocatore2.stato = 0

                # Imposto i turni casualmente
                value = random.randint(0, 1)

                if value == 0:
                    game.giocatore1.turno = 0
                    game.giocatore2.turno = 1
                    message_g1 = f"Indovina l'espressione dell'altro giocatore (utilizzando un audio)\nLe emozioni possibili sono: {self.__emotion_string}"
                    message_g2 = "Invia una foto con una espressione"
                    g_deve_inviare = game.giocatore2
                else:
                    game.giocatore1.turno = 1
                    game.giocatore2.turno = 0
                    message_g1 = "Invia una foto con una espressione"
                    message_g2 = f"Indovina l'espressione dell'altro giocatore (utilizzando un audio)\nLe emozioni possibili sono: {self.__emotion_string}"
                    g_deve_inviare = game.giocatore1

                bot.send_message(chat_id=game.giocatore1.chatid, text=message_g1)
                bot.send_message(chat_id=game.giocatore2.chatid, text=message_g2)
                g_deve_inviare.bing_search = True

                self.__ask_bing_search(bot, g_deve_inviare)

                game.giocatore1.data = None
                game.giocatore2.data = None
            else:
                if operation['image1'] is None:
                    game.giocatore1.stato = 0
                    game.giocatore1.data = None
                    bot.send_message(chat_id=game.giocatore1.chatid,
                                     text="La foto inviata non è corretta! Inviane un'altra")
                    game.giocatore1.bing_search = True
                if operation['image2'] is None:
                    game.giocatore2.stato = 0
                    game.giocatore2.data = None
                    bot.send_message(chat_id=game.giocatore2.chatid,
                                     text="La foto inviata non è corretta! Inviane un'altra")
                    game.giocatore2.bing_search = True
                else:
                    game.giocatore1.images = []
                    game.giocatore2.images = []

    def __photohandler(self, update, context, downloadPhoto=True):
        chat_id = update.effective_chat.id
        status, game, giocatore = self.in_game(chat_id)
        if status and (giocatore.turno is None or giocatore.turno == 1):
            if downloadPhoto:
                file = context.bot.getFile(update.message.photo[0].file_id)
                f = file.download_as_bytearray()
                giocatore.stato = 1
                giocatore.data = f
            context.bot.send_message(chat_id=giocatore.chatid,
                                     text="La foto è stata ricevuta. Attendi il tuo avversario.")

            if giocatore.turno is None:
                self.check_versus(game, context.bot)
            elif giocatore.turno == 1:
                azureVision = AzureVision(self.__azureVisionToken)
                result, emotion = azureVision.get_emotion(BytesIO(giocatore.data))
                if emotion is not None:
                    giocatore.data = emotion
                    context.bot.send_message(chat_id=giocatore.chatid, text=result)
                    self.check_turno(game, context.bot)
                else:
                    giocatore.stato = 0
                    context.bot.send_message(chat_id=giocatore.chatid, text="La foto inviata non è corretta!. Inviane un'altra")
                    giocatore.bing_search = True

    def __button_handler(self, update, context):
        chat_id = update.effective_chat.id
        _, game, giocatore = self.in_game(chat_id)

        query = update.callback_query
        query.answer()
        messaggio = query.data

        if messaggio == 'bingsearch':
            giocatore.bing_search = True
            # if giocatore.query_search is None:
            context.bot.send_message(chat_id=chat_id, text="Digita il testo da ricercare su bing search")
        else:
            if not giocatore.bing_search:
                return

            context.bot.send_message(chat_id=chat_id, text=f"Hai selezionato l'immagine numero {int(messaggio) + 1}")
            try:
                giocatore.data = self.__get_bytes_from_image(giocatore.images[int(messaggio)])
                giocatore.stato = 1
                giocatore.bing_search = False
                self.__photohandler(update, context, downloadPhoto=False)
            except Exception as ex:
                print(ex)
                context.bot.send_message(chat_id=chat_id, text="L'immagine selezionata non è valida, scegline un'altra")
                giocatore.stato = 0
                giocatore.bing_search = True

    def __text_handler(self, update, context):
        chat_id = update.effective_chat.id
        _, game, giocatore = self.in_game(chat_id)

        if giocatore.bing_search:
            giocatore.query_search = update.effective_message.text

        try:
            self.__get_images_from_bing_search(chat_id, giocatore, context.bot, giocatore.query_search)
        except Exception as ex:
            print(ex)

    def __get_bytes_from_image(self, pic_url):
        image = Image.open(requests.get(pic_url, stream=True).raw)

        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        data = img_byte_arr.getvalue()
        img_byte_arr.close()

        return data

    def __get_images_from_bing_search(self, chat_id, giocatore, bot, search):
        # print(giocatore.bing_search)
        # Se il giocatore non può cercare ritorna
        if not giocatore.bing_search:
            return

        # result = ['https://tse4.mm.bing.net/th?id=OIP.4jKN9sOPEM8xFcvyxBPITgHaEK&pid=Api',
        #           'https://tse3.explicit.bing.net/th?id=OIP.uzz_7NwUyiTG5Ir82EL23AHaJV&pid=Api',
        #           'https://tse4.mm.bing.net/th?id=OIP.Qd2uMLSnqxhBKjhMLQWargHaE8&pid=Api',
        #           'https://tse1.mm.bing.net/th?id=OIP.I2wJKDfbDYs9d4BcPOQmIgHaE8&pid=Api',
        #           'https://tse2.mm.bing.net/th?id=OIP.vsCKW0UYiZA9dEYyI9nOHAHaLD&pid=Api',
        #           'https://tse2.mm.bing.net/th?id=OIP.zWV5D0YW_lWrJfgSamll-wHaJD&pid=Api',
        #           'https://tse1.mm.bing.net/th?id=OIP.7ktjWUja8soGhZP-oBtvcwHaE8&pid=Api',
        #           'https://tse1.mm.bing.net/th?id=OIP.CoD1nDs_6d3rtBwG0GIw9gHaLH&pid=Api',
        #           'https://tse2.mm.bing.net/th?id=OIP.MIL2Qg8qBnuHWVkkM8RXdwHaE8&pid=Api',
        #           'https://tse4.mm.bing.net/th?id=OIP.M8GOWAgeUFo7oRsIKWm-TgHaF4&pid=Api']

        s = AzureBingService(self.__azureBingToken)
        result = s.bingSearch(search)
        result = result[:10]
        keyboard = InlineKeyboardMarkup(self.__format_keyboard(giocatore, bot, chat_id, result, 4))

        # Chiedo quale immagine si vuole utilizzare
        bot.send_message(chat_id=chat_id, text="Seleziona un'immagine", reply_markup=keyboard)

    def __format_keyboard(self, giocatore, bot, chat_id, result, num_elements) -> list:
        keyboard = []

        # Aggiungo i prodotti nella lista a tre alla volta
        element = 0
        tmp_list = []
        contatore_reale_foto = 0
        # Svuoto la vecchia lista di immagini
        giocatore.images = []
        for indice, foto in enumerate(result):
            try:
                bot.send_photo(chat_id=chat_id, photo=foto, caption=f"Foto numero {contatore_reale_foto + 1}")
                tmp_list.append(InlineKeyboardButton(text=f"Foto {contatore_reale_foto + 1}", callback_data=contatore_reale_foto))
                giocatore.images.append(foto)
                contatore_reale_foto += 1
                element += 1
                # print(f"Foto: {foto}")
                if element == num_elements:
                    keyboard.append(tmp_list)
                    tmp_list = []
                    element = 0
            except Exception as ex:
                print(ex)

        if tmp_list.__len__() != 0:
            keyboard.append(tmp_list)

        return keyboard

    def __stop(self, update, context):
        chat_id = update.effective_chat.id
        status, game, player = self.in_game(chat_id)
        if status and game == 'waiting':
            self.__wait = []
            context.bot.send_message(chat_id=chat_id, text="Hai annullato la ricerca della partita.")
        elif status:
            if game.giocatore1.chatid == player.chatid:
                msg1 = f"Hai annullato la partita. Punteggio finale:\nIl tuo punteggio {game.giocatore1.punteggio}\nIl punteggio del tuo avversario {game.giocatore2.punteggio}"
                msg2 = f"Il tuo avversario ha annullato la partita. Punteggio finale:\nIl tuo punteggio {game.giocatore2.punteggio}\nIl punteggio del tuo avversario {game.giocatore1.punteggio}"
            else:
                msg2 = f"Hai annullato la partita. Punteggio finale:\nIl tuo punteggio {game.giocatore2.punteggio}\nIl punteggio del tuo avversario {game.giocatore1.punteggio}"
                msg1 = f"Il tuo avversario ha annullato la partita. Punteggio finale:\nIl tuo punteggio {game.giocatore1.punteggio}\nIl punteggio del tuo avversario {game.giocatore2.punteggio}"

            context.bot.send_message(chat_id=game.giocatore1.chatid, text=msg1)
            context.bot.send_message(chat_id=game.giocatore2.chatid, text=msg2)
            self.__games.remove(game)
        else:
            context.bot.send_message(chat_id=chat_id, text="Non sei in attesa di nessuna partita.")


    def __start(self, update, context):
        #OTTENGO IL CHAT ID
        id = update.effective_chat.id
        context.bot.send_message(chat_id=id, text="Benvenuto al \"The Emotion Game\", attendi un avversario prima di iniziare a giocare!")

        status, _, _ = self.in_game(id)
        if not status:
            self.__wait.append(id)
            if len(self.__wait) == 2:
                random.shuffle(self.__wait)
                game = Game(*self.__wait)
                self.__games.append(game)
                self.__wait = []
                context.bot.send_message(chat_id=game.giocatore1.chatid, text="Invia una tua foto per iniziare")
                context.bot.send_message(chat_id=game.giocatore2.chatid, text="Invia una tua foto per iniziare")

                self.__ask_bing_search(context.bot, game.giocatore1)
                self.__ask_bing_search(context.bot, game.giocatore2)

        # print(self.__games)

    def __ask_bing_search(self, bot, giocatore):
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text="Cerca su Bing", callback_data="bingsearch")]])

        bot.send_message(
            chat_id=giocatore.chatid,
            text="Oppure utilizza bing search",
            reply_markup=keyboard
        )

    def __register_function(self, functions: list):
        for function in functions:
            if type(function) is not HandlerFunction:
                raise Exception('[ERROR] __register_function take a list of HandlerFunction objects.')
            # Aggiungo gli handler
            self.__dispatcher.add_handler(CommandHandler(function.name, function.callback))

    def __audio_handler(self, update, context):
        chat_id = update.effective_chat.id
        status, game, giocatore = self.in_game(chat_id)
        # print("Turno: ", giocatore.turno)
        if status and giocatore.turno == 0:
            # 1. Ottengo il file id del messaggio
            file_id = update.message['voice']['file_id']

            risposta = self.__getSpeechMessage(file_id).lower()
            if risposta in self.__emotion:
                # 3.4 Invio il messagigo testuale in chat
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"La tua risposta è: {risposta}")
                # print(f'[{update.message.chat.id}] {update.message.chat.username} mi ha detto {risposta}')

                giocatore.data = risposta.lower()
                giocatore.stato = 1
                self.check_turno(game, context.bot)
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hai inviato {risposta}.\ninviare un'emozione corretta.")
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"Le emozioni possibili sono: {self.__emotion_string}")

    def check_turno(self, game, bot):
        if game.giocatore1.stato == 1 and game.giocatore2.stato == 1:
            if game.giocatore1.turno == 0:
                self.__controllo_giocatore(game, bot)
                game.giocatore1.turno = 1
                game.giocatore2.turno = 0
            else:
                self.__controllo_giocatore(game, bot)
                game.giocatore1.turno = 0
                game.giocatore2.turno = 1

            game.giocatore1.stato = 0
            game.giocatore2.stato = 0

    def __decreta_vittoria(self, bot, game):
        giocatore_vincitore, giocatore_perdente = game.get_vincitore()
        if giocatore_vincitore is not None and giocatore_perdente is not None:
            message_vittoria = f"La partita è terminata!\nCongratulazioni, hai vinto con un punteggio di " \
                               f"{giocatore_vincitore.punteggio}\nIl tuo avversario ha totalizzato {giocatore_perdente.punteggio} punti"
            message_sconfitta = f"La partita è terminata!\nMi dispiace ma hai perso!\nHai realizzato un punteggio di {giocatore_perdente.punteggio}\n" \
                                f"Il tuo avversatio ha totalizzato {giocatore_vincitore.punteggio} punti"

            _, image = self.__get_winner_image(game, 0 if giocatore_vincitore == game.giocatore1 else 1)

            bot.send_message(chat_id=giocatore_vincitore.chatid, text=message_vittoria)
            bot.send_message(chat_id=giocatore_perdente.chatid, text=message_sconfitta)
            bot.send_photo(giocatore_vincitore.chatid, photo=BytesIO(image))
            bot.send_photo(giocatore_perdente.chatid, photo=BytesIO(image))

            # Rimuovo l'istanza di game
            self.__remove_game(giocatore_vincitore)

            return True

        return False

    def __remove_game(self, g1):
        for game in self.__games:
            if g1.chatid == game.giocatore1.chatid or g1.chatid == game.giocatore1.chatid:
                self.__games.remove(game)

    def __controllo_giocatore(self, game, bot):
        g_deve_indovinare = game.giocatore1 if game.giocatore1.turno == 0 else game.giocatore2
        g_indovinante = game.giocatore2 if game.giocatore2.turno == 1 else game.giocatore1

        risposta = g_deve_indovinare.data
        oracolo = g_indovinante.data
        message1 = "Non hai indovinato!"
        message2 = "Il tuo avversario non ha indovinato!"

        if risposta == oracolo:
            g_deve_indovinare.punteggio += 1
            message1 = f"Hai indovinato!\n"
            message2 = f"Il tuo avversario ha indovinato!\n"

        bot.send_message(chat_id=g_deve_indovinare.chatid,
                         text=f"{message1}\nIl tuo punteggio è di {g_deve_indovinare.punteggio}\n"
                              f"Il punteggio del tuo avversario è di {g_indovinante.punteggio}\n")
        bot.send_message(chat_id=g_indovinante.chatid,
                         text=f"{message2}\nIl tuo punteggio è di {g_indovinante.punteggio}\n"
                              f"Il punteggio del tuo avversario è di {g_deve_indovinare.punteggio}")

        game.giocatore1.bing_search = False
        game.giocatore2.bing_search = False

        # Se NON c'è un vincitore, continua
        if not self.__decreta_vittoria(bot, game):
            bot.send_message(chat_id=g_deve_indovinare.chatid, text=f"Adesso tocca a te inviare la foto! Invia una foto con un'espressione")
            # g_deve_indovinare.bing_search = True
            self.__ask_bing_search(bot, g_deve_indovinare)

            bot.send_message(chat_id=g_indovinante.chatid, text=f"Adesso è il tuo turno! Invia un audio in cui pronunci l'emozione dell'avversario")
            bot.send_message(chat_id=g_indovinante.chatid, text=f"Le emozioni possibili sono: {self.__emotion_string}")

    def __getSpeechMessage(self, file_id):
        risposta = ""

        # 2. Faccio la richiesta a telegram per ottenere l'url del download
        # https://api.telegram.org/bot<token>/getFile?file_id=<file_id>
        request_url = f'https://api.telegram.org/bot{self.__botToken}/getFile?file_id={file_id}'
        request = requests.get(url=request_url)
        response_json = json.loads(request.text)

        # 3. Se la richiesta non fallisce scarico l'audio
        try:
            if response_json['ok']:
                # 3.1 La richiesta è andata bene, scarico il file
                # https://api.telegram.org/file/bot<token>/<file_path>
                # print(response_json['result']['file_path'])
                request_url = f"https://api.telegram.org/file/bot{self.__botToken}/{response_json['result']['file_path']}"
                request = requests.get(url=request_url)

                # 3.2 Salvo il file
                with open('audio.oga', 'wb') as file:
                    file.write(request.content)

                # 3.3 Lo converto da .oga a .wav
                src_filename = os.path.join(os.getcwd(), 'audio.oga')
                dest_filename = os.path.join(os.getcwd(), 'audio.wav')

                # 3.3.3 Lancio un processo che esegue il programma ffmpeg per la conversione
                process = subprocess.run(['ffmpeg', '-i', src_filename, dest_filename, "-y"])
                if process.returncode != 0:
                    raise Exception("Errore in ffmpeg")

                # 3.4 Ottengo il testo da Azure
                service = AzureSpeechService(self.__azureSpeechToken)
                try:
                    risposta = service.speechToText(dest_filename)
                    # Tolgo il '.' finale
                    risposta = risposta[0:risposta.__len__() - 1]
                except Exception as ex:
                    risposta = "Non ho capito"

                # 3.5 Cancello i file .oga e .wav
                try:
                    os.remove('audio.oga')
                    os.remove('audio.wav')
                except Exception:
                    traceback.print_exc()
            else:
                # 3.2 La richiesta è fallita, non è possibile scaricare l'audio
                risposta = "Mi dispiace, in questo momento il servizio non è disponibile. Riprova più tardi"

        except Exception as ex:
            traceback.print_exc()
            # 4 La richiesta è fallita, non è possibile scaricare l'audio
            risposta = "Mi dispiace, in questo momento il servizio non è disponibile. Riprova più tardi"
        finally:
            return risposta

    def __get_winner_image(self, game, winner):
        opened_image = Image.open(BytesIO(game.foto))
        trophy = Image.open("trofeo.png")

        dst = Image.new('RGB', (opened_image.width, opened_image.height), color='white')
        dst.paste(opened_image, (0, 0))
        if winner == 0:
            dst.paste(trophy, (0, opened_image.height - trophy.height))
        else:
            dst.paste(trophy, (opened_image.width - trophy.width, opened_image.height - trophy.height))

        img_byte_arr = BytesIO()
        dst.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return_value = img_byte_arr.getvalue()
        img_byte_arr.close()

        return dst, return_value

    def __unknown(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Scusa, non ho capito il tuo comando")


if __name__ == '__main__':
    try:
        with open("config.yml") as file:
            config = yaml.load(file, Loader=yaml.FullLoader)

        # bot = Bot(config['TelegramBotToken'], config['AzureSpeechToken'], config['AzureBingToken'], config['azureVisionToken'])
        bot = Bot(*[config[key] for key in config])
        bot.start_bot()
    except Exception as ex:
        traceback.print_exc()
        print("Errore durante la lettura del file")
        print(ex)
