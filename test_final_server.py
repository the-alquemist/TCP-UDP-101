#!/usr/bin/env python3

# Server final test script: receive a 34-byte message in two recv(17) calls.
# Usage:
#   python3 server.py [port]
# The matching client reads stdin and sends it through SocketTCP.
import argparse
from pathlib import Path

from socket_tcp import SocketTCP


def main():
    # Parse the optional port argument.
    parser = argparse.ArgumentParser(description="Receive a 34-byte message in two recv(17) calls")
    parser.add_argument("port", nargs="?", type=int, default=8000, help="Server port (default: 8000)")
    args = parser.parse_args()

    # Load the expected 34-byte message from the root input file.
    expected = Path(__file__).with_name("input_34.txt").read_bytes()

    # Create the server socket and start listening.
    server = SocketTCP()
    server.bind(("localhost", args.port))
    print(f"[Server] Listening on localhost:{args.port}...")

    try:
        # Accept the incoming connection and wait for the handshake to finish.
        conn, new_address = server.accept()
        print(f"[Server] Handshake completed! New connection from {new_address}")

        # Read the message in as many recv(buff_size) calls as needed.
        buff_size = 17
        chunks = []
        received = b""
        while len(received) < len(expected):
            chunk = conn.recv(buff_size)
            chunks.append(chunk)
            received += chunk

        # Verify that the split recv returns the complete original payload.
        print(f"[Server] recv() was called {len(chunks)} times with buff_size={buff_size}")
        print(f"[Server] Received {len(received)} bytes: {received!r}")
        if received == expected:
            print("[Server] recv split test: Passed")
        else:
            print("[Server] recv split test: Failed")

        # Close the connection using the server-side close path.
        print(f"[Server] Calling recv_close() for localhost:{args.port}...")
        conn.recv_close()
    finally:
        # Always close the listening socket.
        server.close()


if __name__ == "__main__":
    main()