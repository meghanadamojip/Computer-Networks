import socket
import sys
import argparse

# parse and validate command line arguments
def parse_cli_args():
    parser = argparse.ArgumentParser(description="Chat Client")
    parser.add_argument('--id', required=True, help="Unique Client Identifier")
    parser.add_argument('--port', type=int, required=True, help="Port number for client's listening (1-65535)")
    parser.add_argument('--server', required=True, help="Server's address in IP:PORT format")

    arguments = parser.parse_args()

    #validate the port number
    if arguments.port < 1 or arguments.port > 65535:
        sys.stdout.write("Error: Port must be in the range 1-65535.\n")
        sys.stdout.flush()
        sys.exit(1)

    #validate the server address
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

# send a message to the server and receive response
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

# handle the register command
def register_command(socket_connection, client_id, client_ip, client_port):
    reg_message = f"REGISTER\r\nclientID: {client_id}\r\nIP: {client_ip}\r\nPort: {client_port}\r\n\r\n"
    server_response = send_request(socket_connection, reg_message)
    
    if server_response:
        sys.stdout.write("Registration successful.\n")
        sys.stdout.flush()

# handle the bridge command
def bridge_command(socket_connection, client_id):
    bridge_message = f"BRIDGE\r\nclientID: {client_id}\r\n\r\n"
    server_response = send_request(socket_connection, bridge_message)
    
    if server_response:
        sys.stdout.write("Bridge request successful.\n")
        sys.stdout.flush()

# main function to run the chat client
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

    # display connection info
    sys.stdout.write(f"{args.id} connected to {server_host}:{server_port}\n")
    sys.stdout.write(f"{args.id} running on {socket.gethostbyname(socket.gethostname())}:{args.port}\n")
    sys.stdout.write("Enter one of the following commands: /register, /bridge, or /quit.\n")
    sys.stdout.flush()

    # command processing loop 
    while True:
        sys.stdout.write("> ")
        sys.stdout.flush()
        user_input = sys.stdin.readline().strip()

        if user_input == "/register":
            register_command(client_socket, args.id, socket.gethostbyname(socket.gethostname()), args.port)
        elif user_input == "/bridge":
            bridge_command(client_socket, args.id)
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
