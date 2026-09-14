# Video pipelines

Two offscreen renderers for demo videos. Nothing is captured from the screen:
every frame is computed from cell data and painted the way Foot paints it, so
there are no dropped frames, notifications, or cursor artefacts.

```bash
python3 -m venv .venv && .venv/bin/pip install -r video/requirements.txt
python3 video/opener.py /path/to/omarchy-giants-theme/backgrounds
python3 video/showcase.py examples/giants-color --votes curation/votes/2026-09-14-giants-ada-lovelace.json
```

Outputs land in `.local/video/` (ignored). Copy the mp4s wherever you need
them. Requires ImageMagick, ffmpeg, `ttfx`, and `$OMARCHY_PATH/logo.txt`
(the stock screensaver logo, used as the opener's final picture).

## opener.py

Accelerating full-screen colour slides (2 s, 1 s, 0.75 s … 0.1 s), the last
portrait shrinks into its slot in a 4/4/3/3/3 grid, the remaining tiles pop
in, a blackhole consumes the grid and explodes into the stock logo doubled to
2×2 cells per glyph. Canvas 210×58 cells at 9×20 px, the size-11 Foot grid.
The blackhole is TerminalTextEffects 0.15.0 (MIT) with three overrides in
`blackhole.py`: characters keep their glyph, their colour, and their starting
position, and the explosion targets are swapped for the logo. Frames are
cached under `OUT/cache`; delete `cache/blackhole` to recompute the effect.

## showcase.py

The opener, then one `ttfx` effect per artwork from a text collection.
Effects are recorded through a pseudo-terminal at the screensaver grid
(137×36, Foot size 18) with colour kept, exactly what the colour renderer
shows. Anything longer than `--target` seconds (5) is time-compressed by
sampling the recording; `--cap` (10) is a hard limit. Each segment ends with a
`--hold` (1.5 s). With `--votes`, the yes votes from the curation tool are assigned to
artworks in the order they appear in the file, and any beyond the number of
artworks are unused; `--effects` gives an explicit ordered list (the built-in
default is the hand-ordered 17 used for the September 2026 showcase, which
leaves out the four slowest votes). Segments
are cached under `OUT/segments`.

## render.py

The painter: block elements as filled rectangles, everything else in
JetBrainsMono Nerd Font. Used by both pipelines through worker processes.

Recordings and frames derived from third-party artwork stay local.
