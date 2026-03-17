from http.server import HTTPServer, BaseHTTPRequestHandler
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        print("------------- POST BODY ------------")
        print(body.decode('utf-8'))
        print("------------------------------------")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"id":"1","model":"mock","choices":[{"message":{"content":"A"}}]}')

httpd = HTTPServer(('localhost', 8080), SimpleHTTPRequestHandler)
print("Listening on 8080...")
httpd.serve_forever()
