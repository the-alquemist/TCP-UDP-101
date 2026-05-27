# SocketTCP — TCP/UDP Networking - CC4303

Custom TCP-like networking project implemented over UDP with a small SocketTCP abstraction, handshake, stop-and-wait delivery, and close protocols. Includes test scripts for client/server interaction, payload sending/receiving, and connection teardown.

---

## Overview

`socket_tcp.py`:

- Provides a lightweight TCP-style interface on top of UDP
- Implements `bind()`, `connect()`, `send()`, `recv()`, `close()`, `recv_close()`, and `accept()`
- Uses a custom segment format with `SYN`, `ACK`, `FIN`, `seq`, and payload bytes
- Supports a 16-byte chunking strategy for outgoing data
- Buffers incoming payloads so `recv(buffer_size)` can return partial message data across multiple calls

`test_final_client.py`:

- Reads a file from stdin and sends it to the server
- Uses `close()` on the client side
- Supports optional `host` and `port` arguments

`test_final_server.py`:

- Listens for a client connection
- Receives a payload in repeated `recv(17)` calls until the full message is reconstructed
- Uses `recv_close()` on the server side
- Verifies the received payload against `input_34.txt`

`tests/`:

- Main test scripts are in the root directory for clarity and simplicity
- Contains additional beta and unit-style scripts for handshake, send, recv, and close scenarios

---

## How It Works

### General Flow

1. Start the server socket and bind it to `localhost:8000`.
2. Wait for a client `SYN` packet.
3. Complete the handshake using a `SYN` / `SYN-ACK` / `ACK` exchange.
4. For sending data:
   - Split payloads into 16-byte chunks
   - Send each segment with a simple stop-and-wait retry strategy
   - Wait for matching `ACK`s before moving to the next chunk
5. For receiving data:
   - Read the length segment first
   - Buffer incoming payload data until the requested `buffer_size` can be satisfied
   - Return partial data if the current call only needs part of the message
6. For closing:
   - Client side uses `close()`
   - Server side uses `recv_close()`
   - Both sides exchange `FIN` / `FIN+ACK` / final `ACK` style messages
7. If packets are lost, the implementation retries using timeouts and retransmissions.

### Data Handling Strategy

1. Outgoing payloads are encoded as UTF-8 if the message is a string.
2. The first sent segment carries the total payload length.
3. The rest of the payload is divided into 16-byte chunks.
4. `recv(buffer_size)` stores partially received data in an internal buffer.
5. The server test can call `recv(17)` repeatedly until the whole message is reconstructed.

---

## Usage

### Environment Setup

This project is intended to run with the default Python 3.x installation and operative system's native socket, time and path imports. No virtual environment is required. Tested with Python 3.14.4.

```bash
python3 --version
```

### Run the Server Test

```bash
python3 test_final_server.py <optional_port>
```

### Run the Client Test

```bash
python3 test_final_client.py <optional_host> <optional_port> < input_34.txt
```

The client refuses to start unless stdin is redirected or piped, so the `< input_34.txt` part is required.

### Optional Test Files

```bash
python3 test_final_client.py <optional_host> <optional_port> < input_30.txt
```

### Beta Tests

```bash
python3 other_tests/test_beta_server.py <optional_port>
python3 other_tests/test_beta_client.py <optional_port>
```

---

## Notes

- The project listens on `localhost` and port `8000` by default
- The custom protocol uses UDP underneath
- The server-side close path is `recv_close()`
- The client-side close path is `close()`
- The outgoing chunk size is fixed at `16` bytes
- The recv split test uses `buff_size = 17` so the payload must be reconstructed across multiple `recv()` calls
- `input_34.txt` is used for the split-recv scenario
- `input_30.txt` is another human-readable sample input

Edge cases discovered during development include handshake packet loss (requiring retransmit), loss of the handshake final ACK, duplicate segments, split `recv()` behavior when `buffer_size < message_length`, final-segment ACK loss, loss or reordering of the closing `FIN`/ACK exchange, and stray packets arriving from different source ports during close. `socket_tcp.py` already handles many of these: handshake retries (including retransmit of the final ACK), duplicate-segment ACKing, 16-byte chunking with buffered `recv()`, and a final-segment timeout fallback. The test scripts demonstrate the expected behavior and verify correctness against known inputs. The design choices aim to balance simplicity, reliability, and clarity for educational purposes while adhering to TCP-like semantics over UDP.

Testing with simulated loss: to reproduce packet loss and delayed delivery on the loopback interface use `tc netem`. Example (loss + delay):

```bash
sudo tc qdisc add dev lo root netem loss 20.0% delay 0.5s
```

Remove the rule when finished with:

```bash
sudo tc qdisc del dev lo root
```
---

## Key Design Choices

- **UDP transport with TCP-like semantics**
  - The implementation keeps the socket API simple while emulating connection-oriented behavior.

- **Handshake before data transfer**
  - `connect()` and `accept()` complete a lightweight connection setup before data is exchanged.

- **Stop-and-wait reliability**
  - Each segment waits for a matching `ACK` before the next one is sent.

- **Buffered receive path**
  - `recv(buffer_size)` can return partial data and continue across multiple calls.

- **Separate client and server close paths**
  - The client uses `close()` and the server uses `recv_close()`.

- **Pedagogical test scripts**
  - The root-level scripts are meant to demonstrate the protocol behavior clearly and simply.