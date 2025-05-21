import http.server
import socketserver
import base64
import os
import argparse
from functools import partial

# --- Configuration ---
DEFAULT_PORT = 8080
DEFAULT_USERNAME = "dvcuser"
DEFAULT_PASSWORD = "yoursecurepassword" # CHOOSE A STRONG PASSWORD!
# --- End Configuration ---

class AuthHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, username=None, password=None, directory=None, **kwargs):
        self.username = username
        self.password = password
        self.auth_key = base64.b64encode(f"{username}:{password}".encode()).decode()
        # The 'directory' argument is standard for SimpleHTTPRequestHandler from Python 3.7+
        super().__init__(*args, directory=directory, **kwargs)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="DVC Remote"')
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Authentication required.")

    def do_GET(self):
        auth_header = self.headers.get("Authorization")
        if auth_header is None or auth_header != f"Basic {self.auth_key}":
            self.do_AUTHHEAD()
        else:
            super().do_GET()

def run_server(port, username, password, serve_directory):
    if not os.path.isdir(serve_directory):
        print(f"Error: Directory to serve '{serve_directory}' does not exist.")
        return

    print(f"Serving DVC cache from: {os.path.abspath(serve_directory)}")
    print(f"Local URL: http://localhost:{port}")
    print(f"Username: {username}")
    print(f"Password: {password} (Ensure this is strong!)")
    print("Point your ngrok tunnel to this local port.")

    handler_class = partial(AuthHTTPRequestHandler,
                            username=username,
                            password=password,
                            directory=serve_directory)

    with socketserver.TCPServer(("", port), handler_class) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple HTTP server with Basic Auth for DVC cache.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run the server on.")
    parser.add_argument("--user", default=DEFAULT_USERNAME, help="Username for Basic Auth.")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password for Basic Auth.")
    parser.add_argument("--dir", required=True, help="Absolute path to the .dvc/cache directory to serve.")
    
    args = parser.parse_args()
    run_server(args.port, args.user, args.password, args.dir)
