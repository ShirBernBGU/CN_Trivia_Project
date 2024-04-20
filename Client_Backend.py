import socket
import struct
import threading
import time
from inputimeout import inputimeout, TimeoutOccurred
from Colors import bcolors


class TriviaClient:
    def __init__(self, udp_port=13117, name="Hi"):
        self.client_name = name
        self.udp_port = udp_port
        self.listener_socket = None
        self.listening_thread = None
        self.tcp_socket = None
        self.server_address = None
        self.server_port = None
        self.stop_listening_flag = False  # Flag to control the loop in listen_for_broadcasts

    def listen_for_broadcasts(self):
        """Listen for UDP broadcasts from the server and connect to it when a message is received."""
        # Create a UDP socket
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Enable port reusability and bind to the broadcast port
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener_socket.bind(('', self.udp_port))

        print(f"{bcolors.BRIGHT_BLUE}Listening for broadcasts on port {self.udp_port}...{bcolors.ENDC}")

        while not self.stop_listening_flag:
            try:
                data, address = self.listener_socket.recvfrom(1024)  # Receive broadcast
                # Unpack the received data
                magic_cookie, message_type, server_name, server_port = struct.unpack('!IB32sH', data)
                server_name = server_name.decode().rstrip('\x00')  # Remove padding
                if magic_cookie == 0xabcddcba and message_type == 0x2:
                    print(f"{bcolors.GREEN}Received offer from {address}: {server_name}, Port: {server_port}{bcolors.ENDC}")
                    # Save the server address and port for later use
                    self.server_address = address[0]
                    self.server_port = server_port
                    self.connect_to_server()
                    
                    break
                else:
                    print(f"Received message from {address} but with incorrect magic cookie or message type.")

            except struct.error:
                print(f"Received message from {address} with incorrect format.")
            except OSError:
                # This exception handles the case where the socket is closed, thus breaking out of the loop
                break

        self.stop_listening()

    def start_listening(self):
        """Start listening for broadcasts from the server."""
        # Use a separate thread to listen for broadcasts so it doesn't block the main thread
        self.listening_thread = threading.Thread(target=self.listen_for_broadcasts)
        self.listening_thread.start()

    def stop_listening(self):
        """Stop listening for broadcasts and close the socket."""
        self.stop_listening_flag = True  # Set the flag to stop the loop in listen_for_broadcasts
        if self.listener_socket:
            self.listener_socket.close()

    def connect_to_server(self):
        """Connect to the server using TCP."""
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect((self.server_address, self.server_port))
            print(f"{bcolors.BRIGHT_MAGENTA}Connected to server {self.server_address} on port {self.server_port}{bcolors.ENDC}")
            # Here you can add the logic to handle communication with the server.

            # Send the client's name
            if not self.client_name.endswith('\n'):
                self.client_name += '\n'
            self.tcp_socket.sendall(self.client_name.encode('utf-8'))

            # Wait for and print the welcome message from the server
            welcome_message = self.tcp_socket.recv(1024).decode('utf-8')  # Adjust buffer size if necessary
            print(f"{bcolors.BRIGHT_CYAN}{welcome_message}{bcolors.ENDC}")

        except Exception as e:
            print(f"Failed to connect to server {self.server_address} on port {self.server_port}: {e}")

    def handle_server_messages(self):
        """Handle messages received from the server."""
        self.tcp_socket.settimeout(None)  # Ensure the socket is in blocking mode
        while True:
            try:
                message = self.tcp_socket.recv(1024).decode('utf-8').strip()
                if message:
                    print(f"{bcolors.BRIGHT_CYAN}{message}{bcolors.ENDC}")
                    if message.startswith("Question"):
                        self.answer_question()
                    if message.startswith(f"{bcolors.BG_BRIGHT_WHITE}The winner is"):
                        print(f"{bcolors.BRIGHT_RED}Game Over!{bcolors.ENDC}")
                        break

                else:
                    print("Server closed the connection.")
                    self.tcp_socket.close()

            except Exception as e:
                print(f"{bcolors.BRIGHT_RED}Server Disconnected{bcolors.ENDC}")
                self.tcp_socket.close()
                break  # Or attempt to reconnect
                

    def answer_question(self):
        """
        Wait for user input and send it to the server.
        This function uses the inputimeout package to wait for user input with a timeout.
        """
        try:
            start_time = time.time()
            answer = inputimeout(prompt="Your answer here: ", timeout=10)  # Wait for input with a 10-second timeout
            while answer.upper() not in ["Y", "T", "1", "N", "F", "0"]:
                print("Invalid answer. Try again.")
                answer = inputimeout(prompt="Your answer here: ", timeout=start_time + 10 - time.time())
            self.tcp_socket.sendall(answer.encode())
        except TimeoutOccurred:
            print(f"{bcolors.YELLOW}Time's up! No answer was provided.{bcolors.ENDC}")
            self.tcp_socket.sendall("p".encode())  # Send a placeholder answer
            # Optionally, send a message to the server indicating a timeout/no answer
            # This is useful if you want to track client responses, even timeouts, on the server side.
        
    # def answer_question(self):
    #     try:
    #         self.tcp_socket.settimeout(10)
    #         answer = input("Your answer here: ").strip().upper()
    #         while answer not in ["Y", "T", "1", "N", "F", "0"]:
    #             print("Invalid answer. Try again.")
    #             answer = input("Your answer here: ").strip().upper()
    #         self.tcp_socket.sendall(answer.encode())
    #     except socket.timeout:
    #         print(f"{bcolors.YELLOW}Time's up! No answer was provided.{bcolors.ENDC}")
    #         answer = "p"
    #         self.tcp_socket.sendall(answer.encode())


    def game_flow(self):
        """Start the game flow by listening for broadcasts, connecting to the server, and handling messages."""
        self.start_listening()
        self.listening_thread.join()
        self.handle_server_messages()

    def start_game(self):
        try:
            self.game_flow()

        finally:
            print(f"{bcolors.BG_CYAN}End of program.{bcolors.ENDC}")
