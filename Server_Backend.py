import socket
import time
import random
from Questions import TriviaQuestions
import struct
import threading
from Colors import bcolors
import pandas as pd
import os

class TriviaServer:
    def __init__(self, udp_port=13117, tcp_port=13118, server_name="YOLO"):
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.server_ip = socket.gethostbyname(socket.gethostname())

        ### Game variables:
        self.server_name = server_name.ljust(32, '\x00')  # 32 bytes

        # Questions:
        self.trivia_questions = TriviaQuestions()
        self.curr_question = None
        self.curr_answer = None
        self.question_duration = 10  # seconds
        self.i = 0
        self.round_active = False  # Indicates if a round is currently active
        self.round_timer = None
        self.clients_responded = set()  # Set to track clients who have responded

        # Additional attributes
        self.broadcast_interval = 1  # seconds
        self.running = True
        self.broadcasting = False  # Specifically controls broadcasting
        self.broadcast_thread = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # TCP server initialization
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []  # To keep track of connected clients
        self.disqualified = []  # To keep track of disqualified clients
        self.this_round_disqualified = []  # To keep track of disqualified clients in the current round

        # Events
        self.round_ended = threading.Event()  # Event to signal the end of a round
        self.broadcast_event = threading.Event()  # Event to signal broadcasting
        self.countdown_event = threading.Event()  # Event to signal countdown
        self.enough_clients_event = threading.Event()  # Event to signal enough clients
        self.broadcast_stop_event = threading.Event()  # Define this in the __init__ method

        # Statistics
        self.statistics = {
            'game_id': "",
            'client_name': "",
            'client_score': "",
            'total_questions': "",
            'total_clients': ""
        }
        self.csv_file_path = 'Stat.csv'
        self.ensure_csv_initialized()
        self.stat_df = pd.read_csv(self.csv_file_path)
        self.game_id = self.initialize_game_id()

    def initialize_game_id(self):
        """ Initialize game_id by reading from an existing CSV or starting new. """
        try:
            return self.stat_df['game_id'].max() + 1
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return 1

    def broadcast_udp(self):
        """
        Broadcast the server's existence using UDP.
        Tells potential clients the server is available for connection, and the connection details.
        """
        # Added: Define the packet format according to the requirements
        magic_cookie = 0xabcddcba
        message_type = 0x2
        # Changed: Pack the message using struct to conform to the specified packet format
        packet = struct.pack('!IB32sH', magic_cookie, message_type, self.server_name.encode('utf-8'), self.tcp_port)

        while self.broadcasting:
            # Changed: Send the packed message instead of a simple string message
            message = f"Server started, listening on {self.server_ip}:{self.tcp_port}"
            self.udp_socket.sendto(packet, ('<broadcast>', self.udp_port))
            print(f"Broadcasted: {message} {self.udp_port}")
            time.sleep(1)  # Send the broadcast every second

    ### TCP Server methods
    def start_tcp_server(self):
        self.tcp_socket.bind((self.server_ip, self.tcp_port))
        self.tcp_socket.listen()
        print(f"TCP server listening on {self.server_ip}:{self.tcp_port}")

        while self.running:
            self.tcp_socket.settimeout(1)  # Set a timeout for accept to allow periodic check of self.running
            try:
                client_socket, client_address = self.tcp_socket.accept()
                print(f"Accepted connection from {client_address}")

                # Handle the client connection in a separate thread
                client_thread = threading.Thread(target=self.handle_client_connection,
                                                 args=(client_socket, client_address))
                client_thread.start()

            except socket.timeout:
                pass  # Ignore timeouts, just loop again if needed

            except Exception as e:
                # print(f"Error accepting connections: {e}")
                break

    def handle_client_connection(self, client_socket, client_address):
        """
        Handle the client connection for receiving messages.
        :param client_socket: socket
        :param client_address: tuple
        :return: None
        """
        # Initialize client info structure
        client_info = {
            'socket': client_socket,
            'address': client_address,
            'name': None,  # Will be updated after receiving the name
            'thread': threading.current_thread(),  # Current thread handling this connection
            'score': 0,
            'last_correct_round': 0
        }

        # Try to add a lock for thread safety when modifying shared resources
        client_list_lock = threading.Lock()

        try:
            # Receive the client's name as the first message
            client_name = client_socket.recv(1024).decode().strip()
            client_info['name'] = client_name

            # Handle user name is already taken:
            with threading.Lock():  # Assume you have a threading.Lock() instance for thread-safe operations
                if client_name in [client['name'] for client in self.clients]:
                    client_socket.sendall("Name already taken. Wait for someone with your name to leave the server, or disconnect and choose a new name.".encode())
                    client_socket.close()
                    client_info['thread'].join()
                    return

            # Now append the updated client_info to self.clients
            with threading.Lock():  # Assume you have a threading.Lock() instance for thread-safe operations
                self.clients.append(client_info)
                self.countdown_event.set()  # Notify the countdown of a change in the client list
                self.enough_clients_event.set()  # Signal that there are enough clients connected
                self.broadcast_tcp(f"{client_name} connected.")

            print(f"Client {client_name} connected from {client_address}") 

            # Keep the connection alive and listen for messages
            while self.running:
                message = client_socket.recv(1024).decode().strip()

                with threading.Lock():  # Assume you have a threading.Lock() instance for thread-safe operations
                    if not message:
                        break  # Client closed connection or empty message

                    # Save the results for the round:
                    if message.upper() in self.curr_answer:
                        client_info['score'] += 1
                        client_info['last_correct_round'] = self.i
                        res = "correctly!"
                    
                    # Wrong answer:
                    else:
                        res = "incorrectly."
                    
                    print(f"Client {client_info['name']} answered {res} Score: {client_info['score']}, Round: {self.i}")

                    # Check if everyone answered:

        except Exception as e:
            print(f"Error handling connection from {client_info['name']} @ {client_address}: {e}")

        finally:
            
            # Remove the client from the list of connected clients 
            if client_info in self.clients:
                self.clients.remove(client_info)
                self.countdown_event.set()  # Signal that a client has disconnected

            # Trigger Countdown event if the number of clients drops below 2
            if len(self.clients) < 2:
                self.enough_clients_event.clear()  # Clear the event if clients drop below the threshold

            # Ensure the socket is closed to free up resources and prevent memory leaks
            client_socket.close()
            # Use a lock to safely remove the client from the list
            with client_list_lock:
                self.clients = [client for client in self.clients if client['socket'] != client_socket]
            print(f"Client {client_info.get('name', 'Unknown')} @ {client_address} disconnected.")
            self.broadcast_tcp(f"{client_info.get('name', 'Unknown')} disconnected.")

    def stop_server(self):
        """Stop the TCP server and close all client connections."""
        self.running = False
        if self.tcp_socket:
            try:
                self.tcp_socket.close()  # Close the TCP server socket
            except Exception as e:
                print(f"Error closing server socket: {e}")
                
        # Close threads and sockets of connected clients
        if len(self.clients) > 0:
            # close connected clients threads
            for client_info in self.clients: 
                try:
                    if client_info['thread']:
                        client_info['thread'].join()
                except Exception as e:
                    print(f"Error closing client thread: {e}")

            # Close connected clients sockets
            for client_info in self.clients:  
                try:
                    if client_info['socket']:
                        client_info['socket'].close()
                except Exception as e:
                    print(f"Error closing client socket: {e}")
        
        # Close threads and sockets of disqualified clients
        if len(self.disqualified) > 0:
            # Close disqualified clients threads
            for client_info in self.disqualified:  
                try:
                    if client_info['thread']:
                        client_info['thread'].join()
                except Exception as e:
                    print(f"Error closing client thread: {e}")

            # Close disqualified clients sockets
            for client_info in self.disqualified: 
                try:
                    if client_info['socket']:
                        client_info['socket'].close()
                except Exception as e:
                    print(f"Error closing client socket: {e}")
        
        print("Stopped TCP server.")


    def start_broadcasting(self):
        """
        Start broadcasting the server's existence using UDP.
        """
        if not self.broadcasting:
            self.broadcasting = True
            self.broadcast_thread = threading.Thread(target=self.broadcast_udp)
            self.broadcast_thread.start()

            # Start TCP server in a separate thread
            tcp_server_thread = threading.Thread(target=self.start_tcp_server)
            tcp_server_thread.start()

            print("Started broadcasting and TCP server...")

    def stop_broadcasting(self):
        """Stop broadcasting the server's existence using UDP."""
        if self.broadcasting:
            self.broadcasting = False
            self.broadcast_thread.join()
            self.udp_socket.close()     # Added: Close the UDP socket
            print("Stopped broadcasting, the game will start soon.")

    ### Additional methods
    def is_used_port(self, port):
        """
        Check if a port is already in use.
        :param port: int
        :return: bool
        """
        try:
            # Attempt to create a socket on the specified port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return False  # Port is available
        except OSError:
            return True  # Port is already in use

    def find_available_port(self):
        """
        Find an available port for the server to bind to.
        :return: int
        """
        port = random.randint(1024, 64000)
        while self.is_used_port(port):
            port = random.randint(1024, 64000)
        return port

    def broadcast_tcp(self, message):
        """
        Broadcast a message to all connected TCP clients.
        :param message: str
        :return: None
        """
        for client in self.clients:
            client_socket = client['socket']
            try:
                client_socket.sendall(message.encode())
                print(f"Sent message to {client['name']}")
                print(message)
            except Exception as e:
                print(f"Error sending message to {client['name']}: {e}")

    def broadcast_tcp_disqualified(self, message):
        """
        Broadcast a message to all connected TCP clients.
        :param message: str
        :return: None
        """
        for client in self.disqualified:
            client_socket = client['socket']
            try:
                client_socket.sendall(message.encode())
                print(f"Sent message to {client['name']}")
                print(message)
            except Exception as e:
                print(f"Error sending message to {client['name']}: {e}")

    def broadcast_question(self):
        """
        Broadcast the current trivia question to all clients.
        :return: None
        """
        message = f"Question number {self.i}: {self.curr_question}"
        self.broadcast_tcp(message)

    def broadcast_answer(self):
        """
        Broadcast the correct answer to the current trivia question to all clients.
        :return: None
        """
        answer = ""
        if self.curr_answer == ["Y", "T", "1"]:
            answer = "True"
        elif self.curr_answer == ["N", "F", "0"]:
            answer = "False"
        message = f"Answer: {answer}"
        self.broadcast_tcp(message)

    def ensure_csv_initialized(self):
        """Ensure CSV file is initialized with headers if it doesn't already exist."""
        if not os.path.exists(self.csv_file_path) or os.stat(self.csv_file_path).st_size == 0:
            # Only create the file with headers if it does not exist or is empty
            initial_data = {
                'game_id': [0],
                'client_name': [0],
                'client_score': [0],
                'total_questions': [0],
                'total_clients': [0]
            }
            df = pd.DataFrame(initial_data)
            df.to_csv(self.csv_file_path, index=False)
            print("CSV initialized with headers and initial row of zeros.")
        else:
            print("CSV already exists and is not empty.")

    def record_stats(self):
        game_id = self.game_id
        total_questions = self.i  # Assuming trivia_questions holds all questions for a game
        total_clients = len(self.clients) + len(self.disqualified)
        
        stats = []
        for client in self.clients + self.disqualified:
            stats.append({
                'game_id': game_id,
                'client_name': client['name'],
                'client_score': client['score'],
                'total_questions': total_questions,
                'total_clients': total_clients
            })

        # Convert stats to DataFrame
        new_stats_df = pd.DataFrame(stats)
        new_stats_df.to_csv(self.csv_file_path, mode='a', header=False, index=False)
        
        df = pd.read_csv(self.csv_file_path)
        
        # Player who played the most games
        most_games = df['client_name'].value_counts().idxmax()
        most_games_count = df['client_name'].value_counts().max()

        # Calculate win ratios for each player in self.clients and self.disqualified
        max_scores = df.groupby('game_id')['client_score'].transform('max')
        winners = df[df['client_score'] == max_scores]
        win_count = winners['client_name'].value_counts()
        game_count = df['client_name'].value_counts()
        win_ratio = win_count.div(game_count, fill_value=0)

        # Filter win ratio to include only current players and disqualified players
        current_players = [client['name'] for client in self.clients + self.disqualified]
        win_ratio_filtered = win_ratio[current_players]

        # Longest round (game with the most rounds)
        rounds_per_game = df['total_questions']
        max_rounds = rounds_per_game.max()
        # games_with_most_rounds = rounds_per_game[rounds_per_game == max_rounds].index.tolist()

        # Prepare broadcast message
        statistics_message = (
            f"{bcolors.BRIGHT_MAGENTA}Some statistics from the game:\n\n"
            f"Player with the most games: {most_games} (Played {most_games_count} games)\n\n"
            f"Win Ratios:\n{win_ratio_filtered}\n"
            f"\nLongest game ever (game with the most rounds): {max_rounds}{bcolors.ENDC}\n\n"
        )

        # Assume the broadcast_tcp function is correctly implemented to send messages
        self.broadcast_tcp(statistics_message)
        self.broadcast_tcp_disqualified(statistics_message)

    def game_round(self):
        """
        Run a single round of the game.
        :return: None
        """
        print("Starting a new round...")
        self.this_round_disqualified = []  # Reset disqualified clients for the new round
        self.i += 1
        self.round_active = True  # Start the round
        self.update_new_question()
        self.broadcast_question()

        # Start a timer for the question duration
        self.round_timer = threading.Timer(self.question_duration, self.end_round)
        self.round_timer.start()

        # Wait here until the round ends (either by timer or correct answer)
        self.round_ended.wait()  # This will block until the event is set in end_round()

        # After round ends
        self.broadcast_answer()
        scores = self.current_scores()
        print(scores)
        self.broadcast_tcp(scores)
        time.sleep(3)  # Wait a bit before starting the next round

        # Reset the event for the next round
        self.round_ended.clear()

    def end_round(self):
        """
        Ends the current game round.
        """
        if self.round_active:  # Check to prevent multiple calls
            print("Ending the round...")
            self.round_active = False
            self.round_ended.set()  # Signal that the round has ended
            clients_correct = 0

            # Check if any clients answered correctly
            for client in self.clients:
                if client['last_correct_round'] == self.i:
                    clients_correct += 1

            # Handle the case where at least one client answered correctly
            if clients_correct != 0:
                for client in self.clients[:]:
                    if client['last_correct_round'] != self.i:
                        try:
                            # Inform the client that they didn't answer correctly
                            client['socket'].sendall("You are the weak spot. Goodbye!\n".encode('utf-8'))
                            self.disqualified.append(client)
                            self.this_round_disqualified.append(client)
                            # client['socket'].close()  # Close the client's socket
                        except Exception as e:
                            print(f"Error sending message or closing client socket: {e}")
                        finally:
                            # Remove the client from the clients list
                            self.clients.remove(client)
            
            # Handle the case where no clients answered correctly
            else:
                self.broadcast_tcp("No one was correct this round")
                # Add your indented block of code here
                pass

            time.sleep(3)  # Wait a bit before starting the next round


    def update_new_question(self):
        """
        Update the current trivia question and answer.
        :return: None
        """
        question = self.trivia_questions.get_trivia_question_dict()
        self.curr_question = question['question']
        self.curr_answer = question['answer']

    def announce_winner(self):
        """
        Announce the winner of the trivia game.
        :return: None
        """

        # Update the statistics and write to a CSV file
        self.record_stats()

        # Find the client with the highest score
        if self.clients:
            max_score = max([client['score'] for client in self.clients])
            winners = [client['name'] for client in self.clients if client['score'] == max_score]
            if len(winners) == 1:
                message = f"\n{bcolors.BG_BRIGHT_WHITE}The winner is {winners[0]} with a score of {max_score}!{bcolors.ENDC}"
            else:
                message = f"We have a tie between {', '.join(winners)} with a score of {max_score}!"
            self.broadcast_tcp(message)
            self.broadcast_tcp_disqualified(message)
            time.sleep(3) # Wait a bit before stopping the server
        else:
            message = "No clients remained connected to determine a winner :("
            print(message)

    def current_scores(self):
        """
        Get the current scores of all connected clients.
        :return: dict
        """
        scores = {client['name']: client['score'] for client in self.clients}
        # Create a string of scores
        
        score_str = "\n".join([f"{name}: {score}" for name, score in scores.items()])

        this_round_disqualified_str = ",".join([f"{client['name']}" for client in self.this_round_disqualified])
        
        if len(this_round_disqualified_str) == 0:
            return f"\n{bcolors.WHITE}{bcolors.UNDERLINE}Current Scores:{bcolors.ENDC}\n{score_str}\nNo one was disqualified this round.\n"
        else:
            return f"\n{bcolors.WHITE}{bcolors.UNDERLINE}Current Scores:{bcolors.ENDC}\n{score_str}\n{bcolors.UNDERLINE}Disqualified:{bcolors.ENDC} {this_round_disqualified_str}.\n"

    def start_game(self):
        """
        Start the trivia game, adapting to the number of connected clients.
        """

        def broadcast_loop():
            """Continuously broadcast until at least 2 clients connect."""
            while self.running:
                if len(self.clients) < 2:
                    self.start_broadcasting()
                    # Wait until the event is set, indicating that enough clients are connected, or timeout
                    self.enough_clients_event.wait(timeout=self.broadcast_interval)
                    self.enough_clients_event.clear()  # Clear the event for the next check
                else:
                    break  # Stop broadcasting if there are enough clients

        def countdown():
            """Start a 10-second countdown, reset if new client connects or stops if clients drop below 2."""
            self.countdown_event.clear()  # Ensure the countdown event is cleared at the start
            countdown_time = 10
            while countdown_time > 0 and self.running:
                countdown_msg = f"Countdown: {countdown_time} seconds"
                print(countdown_msg)
                self.broadcast_tcp(countdown_msg)  # Broadcast countdown message to all clients
                
                # Wait for 1 second or until the event is set if there is a significant client list change
                self.countdown_event.wait(timeout=1)
                
                # Check conditions after waking up
                if len(self.clients) < 2:
                    self.broadcast_tcp("Countdown aborted: Not enough players.")
                    return False
                
                # Check if the event was set, indicating a client change
                if self.countdown_event.is_set():
                    countdown_time = 10  # Reset the countdown if the client list changed
                    self.countdown_event.clear()  # Clear the event for the next iteration
                
                else:
                    countdown_time -= 1  # Decrement countdown only if no event was set
            return True
        
        
        # Find an available port for the server to bind to:
        if self.is_used_port(self.tcp_port):
            self.tcp_port = self.find_available_port()

        self.running = True
        broadcast_thread = threading.Thread(target=broadcast_loop)
        broadcast_thread.start()
        broadcast_thread.join()  # Wait for the broadcasting thread to ensure 2 clients are connected


        # Countdown to start the game
        ready_to_start_event = threading.Event()  # Event to signal when enough clients are connected
        # Once we have at least 2 clients, perform the countdown
        while self.running:
            # Wait for the event that indicates there are enough clients
            if len(self.clients) >= 2:
                ready_to_start_event.set()  # Signal that we have enough clients
            else:
                ready_to_start_event.clear()  # Not enough clients, clear the event

            # Wait on the event, with a timeout if needed
            ready_to_start_event.wait(timeout=1)  # Adjust timeout based on your needs

            if ready_to_start_event.is_set():
                if countdown():  # Countdown completes without interruption
                    self.stop_broadcasting()
                    names = ", ".join([client['name'] for client in self.clients])
                    self.broadcast_tcp(f"{names}, The trivia game is starting now!")
                    time.sleep(3)  # Wait a bit before starting the game
                    break  # Proceed to the game
                else:
                    print("Client count dropped below 2 during countdown. Resuming broadcast...")
                    # No need to restart the broadcast_thread, let it handle autonomously
            else:
                # Log or handle the condition of not having enough clients
                print("Not enough clients to start the game, waiting...")

        # Start the game rounds
        while self.running:
            self.game_round()

            # Check if the game ended due to lack of clients or a winner
            # If there is only one client left, announce them as the winner
            if len(self.clients) == 1:
                self.running = False
                self.announce_winner()
            # If there are no clients left, end the game
            if len(self.clients) == 0:
                print("All clients left.")
                self.running = False
        
        self.stop_server()
        print("Game over. Server stopped.")

