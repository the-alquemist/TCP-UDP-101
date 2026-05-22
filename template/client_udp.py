import socket
from socket_tcp import SocketTCP

# Client configuration
HOST = "localhost"
PORT = 8000
CHUNK_SIZE = 16

# Read the file path from standard input
file_path = input("Enter the file path to send: ")

my_socket = SocketTCP()

try:
    # Open and read the file
    with open(file_path, "r") as file:
        content = file.read()

    seq = 1
    # Send the content in chunks of maximum 16 bytes, wrapping each chunk in a header
    for i in range(0, len(content), CHUNK_SIZE):
        chunk = content[i:i + CHUNK_SIZE].encode("utf-8")
        is_last = (i + CHUNK_SIZE) >= len(content)
        header = {
            "SYN": 0,
            "ACK": 0,
            "FIN": 1 if is_last else 0,
            "seq": seq,
        }
        segment = SocketTCP.create_segment(header, chunk)
        # send using the underlying UDP socket
        my_socket.socket.sendto(segment, (HOST, PORT))
        seq += 1

    print("File sent successfully.")

except FileNotFoundError:
    print(f"Error: The file '{file_path}' does not exist.")
except Exception as e:
    print(f"Error: {e}")

finally:
    # Close the socket
    my_socket.close()
