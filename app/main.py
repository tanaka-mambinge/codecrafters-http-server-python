import socket


def api_root(soc: socket.socket, url: str):
    res = soc.send(b"HTTP/1.1 200 OK\r\n\r\n")
    print(f"Response: {res}")


def api_not_found(soc: socket.socket, url: str):
    res = soc.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
    print(f"Response: {res}")


def api_echo(soc: socket.socket, url: str):
    # Extract the message from the url
    message = url.split("/echo/")[-1]
    status_line = "HTTP/1.1 200 OK\r\n"
    headers = f"Content-Type: text/plain\r\nContent-Length: {len(message)}\r\n"

    res = soc.send(f"{status_line}{headers}\r\n{message}".encode())
    print(f"Response: {res}")


def generate_static_paths(paths: dict):
    paths = []

    for path in paths.keys():
        if "/*" in path:
            paths.append((path.replace("/*", ""), path))
        else:
            paths.append((path, path))

    return paths


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
            registered_paths[original_path](soc, path)
            path_found = True
            break

    if not path_found:
        api_not_found(soc, path)

    # Close the socket
    soc.close()


if __name__ == "__main__":
    main()
