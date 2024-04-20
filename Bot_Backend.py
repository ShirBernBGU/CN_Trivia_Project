import random
from Client_Backend import TriviaClient


class TriviaBot(TriviaClient):  # Inherits from TriviaClient
    def __init__(self, udp_port=13117, name=""):
        super().__init__(udp_port)  # Initialize the base class
        # Ensure the client_name starts with 'BOT'
        self.bot_names = [
                        "BOTastic",
                        "BOTzilla",
                        "BOTtoMcBOTface",
                        "BOTanist",
                        "BOTanyBay",
                        "BOTburger",
                        "BOTquake",
                        "BOTanical",
                        "BOTimistic",
                        "BOTinator",
                        "BOTleyCrew",
                        "BOTspeare",
                        "BOTtasticVoyage",
                        "BOTterThanYou",
                        "BOTaConstrictor",
                        "BOTyosiyos",
                        "BOTKokakakavka",
                        "BOTWaveCitrus",
                        "BOTleyFool",
                        "BOTaciousD",
                        "BOTfuPanda",
                        "BOTanicGarden",
                        "BOTtlerRocket",
                        "BOTanicalBliss",
                        "BOTtledUp",
                        "BOTaHolic",
                        "BOTamatic",
                        "BOTaRama",
                        "BOTtitude",
                        "BOTonTheRocks",
                        "BOTtropolis",
                        "BOTmageddon",
                        "BOTero",
                        "BOTdacious",
                        "BOTinBlue",
                        "BOTcopter",
                        "BOTalEclipse",
                        "BOTunheim"
                    ]
        self.client_name = random.choice(self.bot_names)  
    def answer_question(self):
        # Override this method if the bot should answer differently
        answer = random.choice(["Y", "N"])  # Randomly choose 'Y' or 'N' as answer
        print(answer)
        self.tcp_socket.sendall(answer.encode())
