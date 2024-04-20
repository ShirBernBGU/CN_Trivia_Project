# Trivia Game System

This project is a multiplayer trivia game system consisting of separate server, client, and bot components. The system allows users to connect to a trivia game hosted on a server, answer trivia questions, and compete against other players and bots.

## Components

The system is divided into the following main components:

1. **Server**: Manages game logic, sends trivia questions to clients, and handles client responses.
2. **Client**: Connects to the server, displays trivia questions to the user, and sends responses back to the server.
3. **Bot**: Automatically connects to the server and answers trivia questions using predefined logic.

## File Structure

- `Server_Backend.py`: Contains the backend logic for the trivia server.
- `Server_Frontend.py`: A simple script to start the server and handle game sessions.
- `Client_Backend.py`: Contains the backend logic for the trivia client.
- `Client_Frontend.py`: A simple script that allows a user to connect to the server and participate in the game.
- `Bot_Backend.py`: Contains the logic for a trivia bot that automatically plays the game.
- `Bot_frontend.py`: Script to run the trivia bot in a game session.
- `Colors.py`: Defines ANSI color codes for beautifying console output.
- `Questions.py`: Contains a list of trivia questions and methods for question handling.
- `Stat.csv`: Stores game statistics and scores.

## How to Run

### Server
To start the trivia game server, run:
```bash
python Server_Frontend.py
```
This will start the server on a predefined UDP port and listen for incoming client connections.

### Client
To participate as a client in the trivia game, run:
```bash
python Client_Frontend.py
```
You can optionally pass your name as an argument to the script or modify the default name in the script.

### Bot
To run a bot that will automatically connect to the trivia server and answer questions, execute:
```bash
python Bot_frontend.py
```

## Dependencies
Ensure you have Python 3.x installed along with the following Python packages:

- socket
- struct
- threading
- time
- inputimeout (install via pip if necessary)

## Features
- Multiplayer trivia game with real-time question and answer handling.
- Supports multiple simultaneous client connections.
- Includes a bot for automated gameplay.
- Colorful console output for better user experience.

  ##### Enjoy!
