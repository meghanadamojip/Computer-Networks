import socket
import sys
import argparse
import signal
import os

# Global variable for the server socket to ensure proper cleanup
server_socket = None

# Handle SIGINT (Ctrl+C) gracefully
def signal_handler(sig, frame):
    global server_socket
    sys.stdout.write("\nShutting down server gracefully (SIGINT).\n")
    sys.stdout.flush()

    try:
        if server_socket:
            sys.stdout.write("Closing server socket...\n")
            sys.stdout.flush()
            server_socket.close()  # Ensure the server socket is closed
            sys.stdout.write("Server socket closed successfully.\n")
            sys.stdout.flush()
    except Exception as error:
        sys.stdout.write(f"Error closing server socket: {error}\n")
        sys.stdout.flush()

    # Exit cleanly with zero exit code
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Parse and validate command-line arguments
def parse_cli_args():
    parser = argparse.ArgumentParser(description="Chat Server")
    parser.add_argument("--port", type=int, required=True, help="Port number to listen on (1-65535)")
    args = parser.parse_args()

    if args.port < 1 or args.port > 65535:
        sys.stdout.write("Error: Port must be in the range 1-65535.\n")
        sys.stdout.flush()
        sys.exit(1)

    return args

# Stores registered clients: {client_id: (ip_address, port, socket)}
registered_clients = {}

# Parse headers from the message
def parse_headers(message):
    headers = {}
    lines = message.split("\r\n")
    for line in lines[1:]:
        if ": " in line:
            key, value = line.split(": ", 1)
            headers[key] = value
    return headers

# Handle REGISTER requests
def handle_register(headers, client_socket):
    client_id = headers.get("clientID")
    ip_address = headers.get("IP")
    port = headers.get("Port")

    # Check if any required information is missing
    if not client_id or not ip_address or not port:
        return "REGACK\r\nStatus: error\r\n\r\n"  # Send error if any data is missing

    # Store the client's information
    registered_clients[client_id] = (ip_address, int(port), client_socket)
    sys.stdout.write(f"REGISTER: {client_id} from {ip_address}:{port} received\n")
    sys.stdout.flush()

    # Send the registration success message back to the client
    return f"REGACK\r\nclientID: {client_id}\r\nIP: {ip_address}\r\nPort: {port}\r\nStatus: registered\r\n\r\n"


# Handle BRIDGE requests
def handle_bridge(headers):
    client_id = headers.get("clientID")

    if not client_id:
        return "BRIDGEACK\r\nclientID:\r\nIP:\r\nPort:\r\n\r\n"

    # Find the first registered client that is not the requester
    for peer_id, (ip, port, _) in registered_clients.items():
        if peer_id != client_id:
            return f"BRIDGEACK\r\nclientID: {peer_id}\r\nIP: {ip}\r\nPort: {port}\r\n\r\n"

    return "BRIDGEACK\r\nclientID:\r\nIP:\r\nPort:\r\n\r\n"

# Handle CHAT requests
def handle_chat(headers):
    sender_id = headers.get("clientID")
    message = headers.get("message")

    # Check if the sender and message are valid
    if not sender_id or not message:
        return "CHATACK\r\nStatus: error\r\n\r\n"

    # Forward the chat message to another client
    forwarded = False
    for peer_id, (ip, port, peer_socket) in registered_clients.items():
        if peer_id != sender_id:  # Exclude the sender from receiving the message
            try:
                # Forward the chat message to the peer in the correct format
                chat_message = f"CHAT\r\nclientID: {sender_id}\r\nmessage: {message}\r\n\r\n"
                peer_socket.sendall(chat_message.encode())  # Send the formatted message
                sys.stdout.write(f"Forwarded chat from {sender_id} to {peer_id}\n")
                sys.stdout.flush()
                forwarded = True
                break  # Send to the first available peer and stop

            except Exception as e:
                sys.stdout.write(f"Error forwarding chat: {e}\n")
                sys.stdout.flush()

    if forwarded:
        return "CHATACK\r\nStatus: delivered\r\n\r\n"
    else:
        return "CHATACK\r\nStatus: no peers available\r\n\r\n"


# Handle individual client connection
def handle_client(client_socket, client_address):
    try:
        while True:
            message = client_socket.recv(1024).decode()
            if not message:
                break

            sys.stdout.write(f"Received from {client_address}: {message.strip()}\n")
            sys.stdout.flush()

            lines = message.split("\r\n")
            request_type = lines[0]
            headers = parse_headers(message)

            if request_type == "REGISTER":
                response = handle_register(headers, client_socket)
            elif request_type == "BRIDGE":
                response = handle_bridge(headers)
            elif request_type == "CHAT":
                response = handle_chat(headers)
            else:
                response = "ERROR\r\nMessage: Unknown request type\r\n\r\n"

            client_socket.sendall(response.encode())
            sys.stdout.write(f"Sent: {response.strip()}\n")
            sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(f"Error handling client: {e}\n")
        sys.stdout.flush()
    finally:
        client_socket.close()

# Main server function
def main():
    global server_socket  # Use global to manage the server socket in signal handling

    args = parse_cli_args()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", args.port))
    server_socket.listen(5)

    sys.stdout.write(f"Server listening on 0.0.0.0:{args.port}\n")
    sys.stdout.flush()

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            sys.stdout.write(f"Connection from {client_address}\n")
            sys.stdout.flush()
            handle_client(client_socket, client_address)
    except KeyboardInterrupt:
        # Ensure graceful shutdown on KeyboardInterrupt
        signal_handler(None, None)
    finally:
        try:
            server_socket.close()
            sys.stdout.write("Server socket closed in finally block.\n")
            sys.stdout.flush()
        except Exception as error:
            sys.stdout.write(f"Error in finally block: {error}\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
