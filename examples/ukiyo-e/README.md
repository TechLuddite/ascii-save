# Ukiyo-e: Hokusai and Hiroshige in colour

Thirty-two Japanese woodblock prints from the Art Institute of Chicago's open-access collection, converted to truecolour quadrant block text. Sixteen are by Katsushika Hokusai, among them The Great Wave, Red Fuji, Shower Below the Summit, the waterfall series, two ghost prints and bird-and-flower prints. Sixteen are by Utagawa Hiroshige, from the Fifty-three Stations of the Tōkaidō and One Hundred Famous Views of Edo. Flat colour and strong outlines make these prints a good fit for colour blocks.

```bash
python3 scripts/validate.py --color examples/ukiyo-e
foot --fullscreen --app-id=ascii-save.preview python3 scripts/preview.py examples/ukiyo-e --seconds 180
```

Colour files contain SGR sequences, so validate them with `--color` and play them with `ttfx --existing-color-handling dynamic`. The stock renderer strips colour. Each artist's prints play roughly in chronological order, Hokusai first.

## Conversion

Each print was converted with `scripts/convert-color.py --cols 137 --rows 34`. A blank line and a plain-text caption ("Artist: Title, Year") follow, so every file fits the stock 137×36 grid at Foot size 18. Most prints use `--trim 10`, which removes the grey scan backdrop and keeps the print's own paper margin. Portrait prints are indented with plain spaces, so the art sits centred above a wider caption. The trim and indent for each work are recorded in `manifest.json`.

Source images are AIC IIIF JPEGs at 1686 px on the long side. See [source credits](SOURCE-CREDITS.md), [artwork notice](ARTWORK-NOTICE.md) and `manifest.json` for provenance, image URLs, source and output hashes, and per-work settings. To regenerate the collection, download each `image_url` in the manifest, check it against `source_sha256`, and convert it with the recorded trim. A different ImageMagick version may produce different output.

## Verification

On 2026-10-02 all 32 files passed `validate.py --color`, and the colour preparer accepted the whole collection in about 0.35 s. A contact sheet of every file was reviewed. Full fullscreen playback of every print has not been watched.
