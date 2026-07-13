import http.server
import socketserver
import os

PORT = 8080
DIRECTORY = r"c:\Users\Ikeda\Desktop\PhysicsScienceCalculation\portal_html"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

# Ensure directory exists
if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)

# Prevent port reuse issues
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving portal at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping portal server...")
        httpd.shutdown()
