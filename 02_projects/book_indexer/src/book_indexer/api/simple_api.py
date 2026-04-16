import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/search":
            query = parse_qs(parsed.query).get("q", [""])[0]

            try:
                result = subprocess.check_output(
                    ["book-index", "search", query],
                    text=True
                )
            except Exception as e:
                result = str(e)

            response = {
                "results": result
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            self.wfile.write(json.dumps(response).encode())

        elif parsed.path == "/openapi.json":
            spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "Book Search API",
                    "version": "1.0.0"
                },
                "paths": {
                    "/search": {
                        "get": {
                            "parameters": [
                                {
                                    "name": "q",
                                    "in": "query",
                                    "required": True,
                                    "schema": {
                                        "type": "string"
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Search results",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "results": {
                                                        "type": "string"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(spec).encode())



def run():
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("Server running on http://localhost:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()