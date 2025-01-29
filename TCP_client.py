import socket
import sys
import argparse

# Parse and validate command line arguments
def parse_cli_args():
    parser = argparse.ArgumentParser(description="Chat Client")
    parser.add_argument('--id', required=True, help="Unique Client Identifier")
    parser.add_argument('--port', type=int, required=True, help="Port number for client's listening (1-65535)")
    parser.add_argument('--server', required=True, help="Server's address in IP:PORT format")

    arguments = parser.parse_args()

    # Validate the port number
    if arguments.port < 1 or arguments.port > 65535:
        sys.stdout.write("Error: Port must be in the range 1-65535.\n")
        sys.stdout.flush()
        sys.exit(1)

    # Validate the server address
    server_parts = arguments.server.split(":")

    if len(server_parts) != 2:
        sys.stdout.write("Error: Server address must be in 'IP:PORT' format.\n")
        sys.stdout.flush()
        sys.exit(1)

    server_host, server_port = server_parts[0], server_parts[1]

    if not server_port.isdigit() or not (1 <= int(server_port) <= 65535):
        sys.stdout.write("Error: Server address must be in 'IP:PORT' format AND be a valid port (1-65535).\n")
        sys.stdout.flush()
        sys.exit(1)

    server_port = int(server_port)

    return arguments, server_host, server_port

# Send a message to the server and receive response
def send_request(socket_connection, outgoing_message):
    try:
        socket_connection.sendall(outgoing_message.encode())
        sys.stdout.write(f"Sent: {outgoing_message.strip()}\n")
        sys.stdout.flush()

        incoming_message = socket_connection.recv(1024).decode()
        sys.stdout.write(f"Received: {incoming_message.strip()}\n")
        sys.stdout.flush()
        return incoming_message

    except Exception as error:
        sys.stdout.write(f"Error: {error}\n")
        sys.stdout.flush()
        return None

# Handle the /register command
def register_command(socket_connection, client_id, client_ip, client_port):
    # Construct the REGISTER message
    reg_message = f"REGISTER\r\nclientID: {client_id}\r\nIP: {client_ip}\r\nPort: {client_port}\r\n\r\n"
    
    # Send the message to the server
    server_response = send_request(socket_connection, reg_message)
    
    # Process the server's response
    if server_response:
        sys.stdout.write("Registration successful.\n")
        sys.stdout.flush()


# Handle the /bridge command
def bridge_command(socket_connection, client_id):
    bridge_message = f"BRIDGE\r\nclientID: {client_id}\r\n\r\n"
    server_response = send_request(socket_connection, bridge_message)

    if server_response:
        sys.stdout.write(f"Bridge request successful. Response: {server_response.strip()}\n")
        sys.stdout.flush()

# Handle the /chat command
def chat_command(socket_connection, client_id, message):
    chat_message = f"CHAT\r\nclientID: {client_id}\r\nmessage: {message}\r\n\r\n"
    server_response = send_request(socket_connection, chat_message)
    if server_response:
        sys.stdout.write("Chat message sent successfully.\n")
        sys.stdout.flush()

# Function to handle incoming chat messages
def handle_incoming_chat(client_socket):
    try:
        # Receive the incoming message (buffer size of 1024)
        message = client_socket.recv(1024).decode().strip()

        # If a message is received, check its format and display
        if message.startswith("CHAT\r\n"):  # Check if it's a chat message
            sys.stdout.write(f"Received chat message: {message}\n")
            sys.stdout.flush()
        else:
            sys.stdout.write("No chat message received.\n")
            sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(f"Error receiving message: {e}\n")
        sys.stdout.flush()

# Main function to run the chat client
def main():
    # parse arguments and validate them
    args, server_host, server_port = parse_cli_args()

    # create the socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect the TCP socket
    connection_successful = False
    if client_socket.connect_ex((server_host, server_port)) == 0:
        connection_successful = True
    else:
        connection_successful = False
        sys.stdout.write(f"Error: Unable to connect to {server_host}:{server_port}\n")
        sys.stdout.flush()

    if not connection_successful:
        client_socket.close()
        return

    # Command processing loop
    while True:
        # Check for incoming chat messages
        handle_incoming_chat(client_socket)

        # Process user input
        sys.stdout.write("> ")
        sys.stdout.flush()
        user_input = sys.stdin.readline().strip()

        if user_input == "/register":
            register_command(client_socket, args.id, socket.gethostbyname(socket.gethostname()), args.port)
        elif user_input == "/bridge":
            bridge_command(client_socket, args.id)
        elif user_input == "/id":
            sys.stdout.write(f"{args.id.strip()}\n")
            sys.stdout.flush()
        elif user_input == "/chat":
            sys.stdout.write("Enter chat message: ")
            sys.stdout.flush()
            chat_message = sys.stdin.readline().strip()
            chat_command(client_socket, args.id, chat_message)
        elif user_input == "/quit":
            sys.stdout.write("Shutting down client.\n")
            sys.stdout.flush()
            break
        else:
            sys.stdout.write(f"Command not found. {user_input}\n")
            sys.stdout.flush()

    # close the TCP socket
    client_socket.close()

if __name__ == "__main__":
    main()
