#!/usr/bin/env python3

# Server final test script: receive a message in repeated recv(buff_size) calls.
# Usage:
#   python3 test_final_server.py [port] expected_file
# Example:
#   python3 test_final_server.py 8000 input_34.txt
# The matching client reads stdin and sends it through SocketTCP.
import argparse
import sys
from pathlib import Path

from socket_tcp import SocketTCP


def main():
    # Parse the optional port argument and optional expected filename.
    parser = argparse.ArgumentParser(description="Receive a message in repeated recv(buff_size) calls and compare against an expected file")
    parser.add_argument("port", nargs="?", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("expected_file", help="Expected input filename in project root (required)")
    args = parser.parse_args()

    # Load the expected message from the requested input file in the same folder as this script.
    expected_path = Path(__file__).with_name(args.expected_file)
    try:
        expected = expected_path.read_bytes()
    except Exception as e:
        print(f"Error: could not read expected file '{expected_path}': {e}", file=sys.stderr)
        sys.exit(1)

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