import socket


def api_root(**kwargs):
    return b"HTTP/1.1 200 OK\r\n\r\n"


def api_not_found(**kwargs):
    return b"HTTP/1.1 404 Not Found\r\n\r\n"


def api_echo(**kwargs):
    # Extract the message from the url
    url = kwargs.get("url")
    message = url.split("/echo/")[-1]
    return (
        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: "
        + str(len(message)).encode()
        + b"\r\n\r\n"
        + message.encode()
    )


def api_user_agent(**kwargs):
    # Extract the user agent from the headers
    headers = kwargs.get("headers")
    user_agent = None
    for header in headers:
        if "User-Agent" in header:
            user_agent = header.split(": ")[1]
            break

    return (
        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: "
        + str(len(user_agent)).encode()
        + b"\r\n\r\n"
        + user_agent.encode()
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

    # Extract headers from the request
    headers = data.decode().split("\r\n")
    print(headers)

    # Check if the path is registered
    registered_paths = {
        "/echo/*": api_echo,
        "/": api_root,
        "/user-agent": api_user_agent,
    }
    static_paths = generate_static_paths(registered_paths)
    path_found = False

    payload = {
        "url": path,
        "headers": headers,
    }

    for static_path, original_path in static_paths:
        # handle exact match
        if path == static_path:
            response = registered_paths[original_path](**payload)
            soc.send(response)
            path_found = True
            break

        # handle wildcard match
        if path.startswith(static_path) and "/*" in original_path:
            response = registered_paths[original_path](**payload)
            soc.send(response)
            path_found = True
            break

    if not path_found:
        response = api_not_found(**payload)
        soc.send(response)

    # Close the socket
    soc.close()


if __name__ == "__main__":
    main()
