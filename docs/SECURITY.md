# Security boundaries

Collections are untrusted data. The selected root may deliberately be a symlink; directory entries may not. Enumeration is nonrecursive, bounded, and uses file descriptors to avoid reopening children through a replaced directory path. Open before validating, use `O_NOFOLLOW` and `O_NONBLOCK`, and check the descriptor is a regular file before reading. Refuse files changing during the read. Private snapshots keep later source changes out of an active playback session.

The pinned preparer accepts up to 4096 directory entries and 128 valid artworks. Each artwork is limited to 64 KiB, 128 lines and 512 code points per line after tab expansion. It normalizes CRLF, requires UTF-8, and rejects Unicode control/format characters except newline and tab. Empty or whitespace-only input is rejected. These checks bound input and exclude terminal escape sequences; they are not a sandbox for the text-effects engine or a boundary against hostile code already running as the same user.

Do not pass artwork names into a shell command string, command substitution, `eval`, a player configuration, or a playlist syntax that can interpret URLs/options. Do not load scripts from the source directory. Keep generated state outside the source; never delete source artwork on reset or uninstall.

The standalone preview owns its renderer child and restores terminal state on ordinary exit/signals. It does not interact with native idle/lock handling. Native integration must ensure renderer failure cannot cancel locking and must avoid spawning a player that inhibits idle.

For future image mode, separately review decoders, decompression limits, network access, resource exhaustion, sandboxing and window lifecycle. A file extension allowlist alone is insufficient. Keep image decoding outside the long-lived desktop shell unless a reviewed design justifies otherwise.

Recordings, screenshots, local logs and third-party artwork remain private by default. Ignore patterns reduce accidental staging; inspect the exact staged files before every public push. Do not force-add visual evidence without explicit user approval.

## Installed Giants renderer

The opt-in native installer uses the pinned preparer both before activation and at playback startup. It never executes artwork, recursively scans it, or decodes raster files. Braille fitting operates on the bounded validated text. The user PATH override is explicit, renderer-only, reversible, and stored outside the collection directory.

Native cleanup uses owned `Popen` children, with TERM followed by bounded KILL/wait. Cross-window dismissal uses Unix datagrams in an owner-only runtime directory rather than signalling PIDs found by name. This is not an isolation boundary against other code already running as the same user. No network service is exposed. Playback failure keeps the screensaver window alive so the idle service does not mistake it for user dismissal. The screensaver is decoration; Omarchy's existing lock service remains the security boundary.
