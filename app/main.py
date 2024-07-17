import socket


def main():
    print("Logs from your program will appear here!")

    # Create a server socket
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    soc, add = server_socket.accept()

    # Respond to the client with http 200 OK response
    res = soc.send(b"HTTP/1.1 200 OK")
    print(f"Response: {res}")


if __name__ == "__main__":
    main()
