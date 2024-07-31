import argparse
import os
import socket
import threading


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


def api_files(**kwargs):
    args = kwargs.get("args")
    url = kwargs.get("url")
    base_dir = args.get("directory")
    file_name = url.split("/files/")[-1]

    if os.path.exists(os.path.join(base_dir, file_name)):
        with open(os.path.join(base_dir, file_name), "wb") as f:
            file_size_bytes = os.path.getsize(f.name)

            return (
                b"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: "
                + str(file_size_bytes).encode()
                + b"\r\n\r\nHello, World!"
            )

    return b"HTTP/1.1 404 Not Found\r\n\r\n"


def generate_static_paths(paths: dict):
    static_paths = []

    for path in paths.keys():
        if "/*" in path:
            static_paths.append((path.replace("/*", ""), path))
        else:
            static_paths.append((path, path))

    return static_paths


def handle_request(server_socket: socket.socket, args: argparse.Namespace):
    soc, addr = server_socket.accept()

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
        "/files/*": api_files,
        "/user-agent": api_user_agent,
        "/": api_root,
    }
    static_paths = generate_static_paths(registered_paths)
    path_found = False

    payload = {
        "url": path,
        "headers": headers,
        "args": args,
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


def main():
    print("Logs from your program will appear here!")

    # Create a server socket
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    # Parse args
    parse = argparse.ArgumentParser()
    # parse.add_argument("--port", type=int)
    args = parse.parse_args()

    # Handle multiple requests using threads
    while True:
        thread = threading.Thread(target=handle_request, args=(server_socket, args))
        thread.start()


if __name__ == "__main__":
    main()
