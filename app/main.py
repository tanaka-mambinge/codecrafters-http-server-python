import socket


def api_root(url: str):
    return b"HTTP/1.1 200 OK\r\n\r\n"


def api_not_found(url: str):
    return b"HTTP/1.1 404 Not Found\r\n\r\n"


def api_echo(url: str):
    # Extract the message from the url
    message = url.split("/echo/")[-1]
    return (
        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: "
        + str(len(message)).encode()
        + b"\r\n\r\n"
        + message.encode()
    )


def generate_static_paths(paths: dict):
    static_paths = []

    for path in paths.keys():
        if "/*" in path:
            static_paths.append((path.replace("/*", ""), path))
        else:
            static_paths.append((path, path))

    return static_paths


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
    registered_paths = {"/": api_root, "/echo/*": api_echo}
    static_paths = generate_static_paths(registered_paths)
    path_found = False

    for static_path, original_path in static_paths:
        if path.startswith(static_path):
            response = registered_paths[original_path](path)
            soc.send(response)
            path_found = True
            break

    if not path_found:
        api_not_found(soc, path)

    # Close the socket
    soc.close()


if __name__ == "__main__":
    main()
