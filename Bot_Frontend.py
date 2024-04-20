from Bot_Backend import TriviaBot

while True:
    bot = TriviaBot()
    print(f"Bots name: {bot.client_name}")
    bot.start_game()
