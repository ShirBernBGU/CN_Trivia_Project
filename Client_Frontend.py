from Client_Backend import TriviaClient

while True:
    # Uncomment this to allow input from the user:
    # name = input("Enter your name: ")
    # Change the name to your name or any other name you want
    name = "Yossi"
    client = TriviaClient(name=name)
    print(f"Client name: {client.client_name}")
    client.start_game()
