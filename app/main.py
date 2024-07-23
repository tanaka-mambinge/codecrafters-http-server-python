import socket


def main():
    print("Logs from your program will appear here!")

    # Create a server socket
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    soc, add = server_socket.accept()

    # Respond to the client with http 200 OK response
    # res = soc.send(b"HTTP/1.1 200 OK\r\n\r\n")
    # print(f"Response: {res}")

    # Extract url path from the request
    data = soc.recv(1024)
    path = data.decode().split()[1]

    # Check if the path is registered
    registered_paths = ["/"]
    if path not in registered_paths:
        res = soc.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
        print(f"Response: {res}")
    else:
        res = soc.send(b"HTTP/1.1 200 OK\r\n\r\n")
        print(f"Response: {res}")

    # Close the socket
    soc.close()


if __name__ == "__main__":
    main()
