import argparse
import gzip
import os
import socket
import threading


def build_header_str(custom_headers: dict, request_headers: dict) -> str:
    header_str = ""
    supported_encoding = ["gzip"]

    for key, value in custom_headers.items():
        header_str += f"{key}: {value}\r\n"

    accept_encodings = request_headers.get("Accept-Encoding", None)

    if accept_encodings is not None:
        for accept_encoding in accept_encodings.split(","):
            if accept_encoding.strip() in supported_encoding:
                header_str += f"Content-Encoding: {accept_encoding}\r\n"
                break

    return header_str


def build_body(body: str, request_headers: dict) -> bytes:
    supported_encoding = ["gzip"]
    accept_encodings = request_headers.get("Accept-Encoding", None)

    if accept_encodings is not None:
        for accept_encoding in accept_encodings.split(","):
            if accept_encoding.strip() in supported_encoding:
                body_compressed = gzip.compress(body.encode())
                return body_compressed

    return body.encode()


def extract_headers(header_str: str) -> dict:
    headers = header_str.split("\r\n")[1:-2]
    headers_dict = {}

    for header in headers:
        if header:
            key, value = header.split(": ")
            headers_dict[key] = value
    return headers_dict


def api_root(**kwargs):
    return b"HTTP/1.1 200 OK\r\n\r\n"


def api_not_found(**kwargs):
    return b"HTTP/1.1 404 Not Found\r\n\r\n"


def api_echo(**kwargs):
    # Extract the message from the url
    url = kwargs.get("url")
    headers = kwargs.get("headers")
    message = url.split("/echo/")[-1]
    response_body = build_body(message, headers)
    response_headers = {
        "Content-Type": "text/plain",
        "Content-Length": str(len(response_body)),
    }

    return (
        b"HTTP/1.1 200 OK\r\n"
        + build_header_str(response_headers, headers).encode()
        + b"\r\n"
        + response_body
    )


def api_user_agent(**kwargs):
    # Extract the user agent from the headers
    headers = kwargs.get("headers")
    user_agent = headers.get("User-Agent", None)

    if user_agent:
        response_headers = {
            "Content-Type": "text/plain",
            "Content-Length": str(len(user_agent)),
        }

        return (
            b"HTTP/1.1 200 OK\r\n"
            + build_header_str(response_headers, headers).encode()
            + b"\r\n"
            + user_agent.encode()
        )

    else:
        return b"HTTP/1.1 400 Bad Request\r\n\r\n"


def api_files(**kwargs):
    args = kwargs.get("args")
    url = kwargs.get("url")
    method = kwargs.get("method")
    body = kwargs.get("body")
    headers = kwargs.get("headers")

    if method == "GET":
        base_dir = args.directory
        file_name = url.split("/files/")[-1]

        if os.path.exists(os.path.join(base_dir, file_name)):
            # open file in read only mode
            with open(os.path.join(base_dir, file_name), "rb") as file:
                file_stats = os.stat(os.path.join(base_dir, file_name))
                file_size_bytes = file_stats.st_size
                file_content = file.read()

                response_headers = {
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(file_size_bytes),
                }

                return (
                    b"HTTP/1.1 200 OK\r\n"
                    + build_header_str(response_headers, headers).encode()
                    + b"\r\n"
                    + file_content
                )

        return b"HTTP/1.1 404 Not Found\r\n\r\n"

    if method == "POST":
        base_dir = args.directory
        file_name = url.split("/files/")[-1]

        # check if body is empty
        if not body:
            return b"HTTP/1.1 400 Bad Request\r\n\r\n"

        # save body as file
        with open(os.path.join(base_dir, file_name), "wb") as file:
            file.write(body.encode())

        return b"HTTP/1.1 201 Created\r\n\r\n"


def generate_static_paths(paths: dict):
    static_paths = []

    for path in paths.keys():
        if "/*" in path:
            static_paths.append((path.replace("/*", ""), path))
        else:
            static_paths.append((path, path))

    return static_paths


def handle_request(soc: socket.socket, args):
    # Extract url path from the request
    data = soc.recv(1024)
    path = data.decode().split()[1]
    method = data.decode().split()[0]
    headers = extract_headers(data.decode())
    body = data.decode().split("\r\n\r\n")[-1] if "\r\n\r\n" in data.decode() else None

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
        "method": method,
        "body": body,
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
    parse.add_argument("--directory", type=str, help="Directory to serve files from")
    args = parse.parse_args()

    # Handle multiple requests using threads
    while True:
        # Accept a connection
        soc, addr = server_socket.accept()
        print(f"Connection from {addr} has been established!")

        # Handle the request in a separate thread
        thread = threading.Thread(target=handle_request, args=(soc, args))
        thread.start()


if __name__ == "__main__":
    main()
