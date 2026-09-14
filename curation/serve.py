"""Local curation server: serves the voting page and clips, records votes.

Binds 127.0.0.1 only. Nothing is uploaded anywhere.

GET  /              -> index.html (next to this file)
GET  /effects.json  -> effects with current votes and per-effect metadata
GET  /frames/E.json -> per-frame cell diffs (gzip on the wire when E.json.gz exists)
POST /vote          -> {"effect": "...", "vote": "y"|"n"|null}; rewrites votes.json

usage: serve.py DIR [--port 8765]
DIR holds frames/*.json[.gz], optional survey.json, and votes.json (created).
"""
import argparse
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def make_handler(directory):
    votes_path = os.path.join(directory, 'votes.json')
    survey_path = os.path.join(directory, 'survey.json')
    frames_dir = os.path.join(directory, 'frames')

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=HERE, **k)

        def log_message(self, fmt, *args):
            sys.stderr.write('%s %s\n' % (self.address_string(), fmt % args))

        def send_json(self, obj, status=200):
            body = json.dumps(obj).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/effects.json':
                votes = load(votes_path, {})
                survey = load(survey_path, {})
                effects = []
                for name in sorted(os.listdir(frames_dir)) if os.path.isdir(frames_dir) else []:
                    if not name.endswith('.json'):
                        continue
                    effect = name[:-5]
                    effects.append({'effect': effect, 'vote': votes.get(effect), 'survey': survey.get(effect, {})})
                return self.send_json(effects)
            if self.path.startswith('/frames/') and self.path.endswith('.json'):
                path = os.path.join(frames_dir, os.path.basename(self.path))
                gz = path + '.gz'
                use_gz = os.path.isfile(gz) and 'gzip' in self.headers.get('Accept-Encoding', '')
                source = gz if use_gz else path
                if not os.path.isfile(source):
                    return self.send_json({'error': 'not found'}, 404)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                if use_gz:
                    self.send_header('Content-Encoding', 'gzip')
                self.send_header('Content-Length', str(os.path.getsize(source)))
                self.end_headers()
                with open(source, 'rb') as f:
                    self.wfile.write(f.read())
                return
            if self.path in ('/', '/index.html'):
                return super().do_GET()
            return self.send_json({'error': 'not found'}, 404)

        def do_POST(self):
            if self.path != '/vote':
                return self.send_json({'error': 'not found'}, 404)
            length = int(self.headers.get('Content-Length', '0'))
            try:
                data = json.loads(self.rfile.read(length))
                effect = str(data['effect'])
                vote = data.get('vote')
                if vote not in ('y', 'n', None) or not effect.replace('_', '').isalnum():
                    raise ValueError
            except (ValueError, KeyError, TypeError):
                return self.send_json({'error': 'bad request'}, 400)
            votes = load(votes_path, {})
            if vote is None:
                votes.pop(effect, None)
            else:
                votes[effect] = vote
            tmp = votes_path + '.tmp'
            with open(tmp, 'w') as f:
                json.dump(votes, f, indent=2, sort_keys=True)
            os.replace(tmp, votes_path)
            return self.send_json({'ok': True, 'votes': votes})

    return Handler


def serve(directory, port=8765):
    server = ThreadingHTTPServer(('127.0.0.1', port), make_handler(os.path.abspath(directory)))
    print(f'curation page: http://127.0.0.1:{server.server_address[1]}/', flush=True)
    return server


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('dir')
    ap.add_argument('--port', type=int, default=8765)
    a = ap.parse_args()
    serve(a.dir, a.port).serve_forever()


if __name__ == '__main__':
    main()
