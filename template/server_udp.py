import socket
from socket_tcp import SocketTCP

# Server configuration
HOST = "localhost"
PORT = 8000

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the address and port
server_socket.bind((HOST, PORT))

print(f"Server listening on {HOST}:{PORT}...\n")

# Receive data from the client and reassemble payloads
message_bytes = bytearray()
while True:
    data, client_address = server_socket.recvfrom(1024)

    # If we receive an empty message, ignore
    if not data:
        continue

    try:
        header, payload = SocketTCP.parse_segment(data)
    except Exception:
        # If parsing fails, skip this packet
        continue

    # Append payload to message buffer
    if payload:
        message_bytes.extend(payload)

    # Print the newly received payload (decoded), flush immediately
    try:
        print(payload.decode("utf-8"), end="", flush=True)
    except Exception:
        # If payload isn't valid text, skip printing
        pass

    # If FIN flag is set, finish receiving
    if header.get("FIN"):
        print("\nTransfer completed.")
        break

server_socket.close()
