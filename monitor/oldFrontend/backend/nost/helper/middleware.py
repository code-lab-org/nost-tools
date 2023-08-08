#!/usr/bin/env python

from werkzeug.wrappers import Request, Response, ResponseStream
from werkzeug.datastructures import Headers


class Middleware():
    def __init__(self, app, origin="*"):
        self.app = app
        self.origin = origin
        self.username = "nost-client"
        self.password = "nost-2021"

    def __call__(self, environ, start_response):

        def add_cors_headers(status, headers, exc_info=None):
            headers = Headers(headers)
            headers.add("Access-Control-Allow-Origin", self.origin)
            headers.add("Access-Control-Allow-Headers",
                        "Origin, Content-Type, Authorization")
            headers.add("Access-Control-Allow-Credentials", "true")
            headers.add("Access-Control-Allow-Methods",
                        "GET, PUT, POST, DELETE")
            return start_response(status, headers.to_wsgi_list())

        if environ.get("REQUEST_METHOD") == "OPTIONS":
            add_cors_headers("200 OK", [("Content-Type", "text/plain")])
            return [b'200 OK']

        request = Request(environ)
        if request.authorization:
            username = request.authorization['username']
            password = request.authorization['password']
            if username == self.username and password == self.password:
                environ['user'] = {'name': 'nost-client'}
                return self.app(environ, add_cors_headers)
        elif len(request.path) >= 5 and request.path[0:6] == '/docs/':
            return self.app(environ, add_cors_headers)

        res = Response(u'Authorization failed',
                       mimetype='text/plain', status=401)
        return res(environ, start_response)
