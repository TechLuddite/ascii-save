import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'curation'))
import curate  # noqa: E402
import frames  # noqa: E402
import serve  # noqa: E402


def write_cast(path, rows=2, cols=4):
    header = {'version': 2, 'width': cols, 'height': rows}
    up = '\x1b[%dA' % rows
    frame1 = up + '\x1b[38;2;255;0;0;48;2;0;0;0m▀▀\x1b[0m  \r\n    '
    frame2 = up + '\x1b[38;2;255;0;0;48;2;0;0;0m▀▀\x1b[38;2;0;255;0;48;2;0;0;255m█\x1b[0m \r\n    '
    frame3 = up + '\x1b[38;2;255;0;0;48;2;0;0;0m▀▀\x1b[38;2;0;255;0;48;2;0;0;255m█\x1b[0m \r\n ▄  '
    lines = [json.dumps(header), json.dumps([0.0, 'o', '\x1b[?25l' + frame1]),
             json.dumps([0.1, 'o', frame2]), json.dumps([0.2, 'o', frame3])]
    Path(path).write_text('\n'.join(lines) + '\n')


class CurationTests(unittest.TestCase):
    def test_frames_emit_only_changed_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            cast = Path(directory) / 'x.cast'
            write_cast(cast)
            data = frames.convert(cast, fps=1000)
            self.assertEqual((data['cols'], data['rows']), (4, 2))
            self.assertEqual(len(data['frames']), 3)
            first = data['frames'][0][1]
            self.assertEqual(first[:8], [0, 0, '▀', 0, 1, 0, '▀', 0])
            self.assertEqual(data['palette'][0], ['ff0000', '000000'])
            second = data['frames'][1][1]
            self.assertEqual(second, [2, 0, '█', 1])
            self.assertEqual(data['palette'][1], ['00ff00', '0000ff'])
            third = data['frames'][2][1]
            self.assertEqual(third, [1, 1, '▄', 2])
            self.assertEqual(data['palette'][2], ['ffffff', '000000'])

    def test_frames_decimate_to_requested_fps(self):
        with tempfile.TemporaryDirectory() as directory:
            cast = Path(directory) / 'x.cast'
            write_cast(cast)
            data = frames.convert(cast, fps=5)  # 0.2 s step keeps first and last frames only
            self.assertEqual([f[0] for f in data['frames']], [0.0, 0.2])

    def test_server_lists_effects_and_records_votes(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / 'frames').mkdir()
            (work / 'frames/wipe.json').write_text('{"frames":[]}')
            (work / 'survey.json').write_text('{"wipe": {"reveals_first": false}}')
            server = serve.serve(str(work), 0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = 'http://127.0.0.1:%d' % server.server_address[1]
                listing = json.load(urllib.request.urlopen(base + '/effects.json'))
                self.assertEqual(listing, [{'effect': 'wipe', 'vote': None, 'survey': {'reveals_first': False}}])
                request = urllib.request.Request(base + '/vote', data=json.dumps({'effect': 'wipe', 'vote': 'y'}).encode(),
                                                 headers={'Content-Type': 'application/json'})
                self.assertEqual(json.load(urllib.request.urlopen(request))['votes'], {'wipe': 'y'})
                self.assertEqual(json.loads((work / 'votes.json').read_text()), {'wipe': 'y'})
                bad = urllib.request.Request(base + '/vote', data=b'{"effect": "../x", "vote": "y"}',
                                             headers={'Content-Type': 'application/json'})
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(bad)
                self.assertEqual(caught.exception.code, 400)
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(base + '/serve.py')
                self.assertEqual(caught.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()

    def test_apply_rewrites_renderer_include_list(self):
        with tempfile.TemporaryDirectory() as directory:
            renderer = Path(directory) / 'renderer'
            renderer.write_text((ROOT / 'scripts/omarchy-screensaver-color').read_text())
            line = curate.apply_votes(renderer, ['wipe', 'beams'])
            self.assertEqual(line, 'include_effects=(wipe beams)')
            text = renderer.read_text()
            self.assertEqual(text.count('include_effects=('), 1)
            self.assertIn('--include-effects "${include_effects[@]}"', text)
            self.assertEqual(subprocess.run(['bash', '-n', str(renderer)]).returncode, 0)

    def test_committed_vote_record_matches_renderer(self):
        votes = json.loads((ROOT / 'curation/votes/2026-09-14-giants-ada-lovelace.json').read_text())
        yes = sorted(k for k, v in votes.items() if v == 'y')
        text = (ROOT / 'scripts/omarchy-screensaver-color').read_text()
        self.assertIn('include_effects=(%s)' % ' '.join(yes), text)


if __name__ == '__main__':
    unittest.main()
