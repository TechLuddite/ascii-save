# Effect curation

Watch every `ttfx` effect on your own artwork in a browser and vote yes or no
on each. The yes list becomes the screensaver's effect rotation.

Everything runs locally. Recordings, clips and votes stay in `.local/curation/`
(ignored by git); the page is served on 127.0.0.1 only.

## Run

```bash
python3 curation/curate.py record examples/giants-color/03-3-ada-lovelace.txt
python3 curation/curate.py serve      # open http://127.0.0.1:8765/
python3 curation/curate.py apply      # writes the yes list into scripts/omarchy-screensaver-color
```

`record` runs each of the 37 effects in a pseudo-terminal of the screensaver's
size (137×36 by default, the stock size-18 Foot grid at 1920×1200), four at a
time, capped at 120 seconds each. Expect about ten minutes. Raw casts are
hundreds of megabytes each because `ttfx` redraws every cell every frame; they
are converted to per-frame cell diffs at 30 fps and deleted unless
`--keep-casts` is given. Pick a colour artwork so the clips match what the
colour renderer shows; the artwork is only ever read.

`serve` lists the effects with your vote marks. Keys: `y` yes, `n` no, `u`
unvote, `j`/`k` or arrows to move, space to pause, `r` to replay. Voting
auto-advances to the next undecided effect. Votes are written to `votes.json`
on every click.

`apply` rewrites the `include_effects=(...)` line in the colour renderer.
Reinstall the renderer wherever the screensaver reads it (see
`docs/LOCAL-INTEGRATION.md`). `list` prints the yes, no and undecided sets.

## Files

- `record.py`: one effect to an asciicast v2 file with real timestamps.
- `frames.py`: asciicast to cell-diff JSON. Assumes the exact `ttfx` output
  shape (cursor-up, then one line per row); it is not a terminal emulator.
- `serve.py` and `index.html`: the local server and canvas player.
- `votes/`: vote records kept for provenance, named by date and artwork.

Recordings of third-party artwork are derived works; keep them local.
