# YouTube Shorts Studio — Streamlit Community Cloud YouTube setup

This build is configured specifically for Streamlit Community Cloud.

## Why the previous build still got 403

YouTube can require PO Tokens for media requests. The yt-dlp documentation
recommends a PO-token provider, and the WebPoClient provider can mint the
video-bound token in a real Chrome/Chromium browser. The provider must be able
to find Chromium; this build therefore passes the browser path explicitly.

## Files required in the GitHub repository

```text
app.py
downloader.py
requirements.txt
packages.txt
processor.py
...
```

Streamlit Community Cloud installs Python packages from `requirements.txt`
and Linux packages from `packages.txt`.

## Current dependencies

`requirements.txt` includes:
- `yt-dlp[default]` for yt-dlp + EJS scripts
- `yt-dlp-getpot-wpc` for automatic PO-token generation
- `deno` (official Deno binary) for YouTube EJS challenges
- application dependencies

`packages.txt` includes:
- `ffmpeg`
- `chromium`

## Important WPC configuration

`downloader.py` automatically looks for Chromium at:

```text
/usr/bin/chromium
/usr/bin/chromium-browser
/usr/bin/google-chrome
/usr/bin/google-chrome-stable
```

You can override this with the Streamlit secret/environment variable:

```text
YOUTUBE_BROWSER_PATH=/path/to/chromium
```

The downloader passes the path to the WPC plugin as:

```text
--extractor-args "youtubepot-wpc:browser_path=/path/to/chromium"
```

## After pushing to GitHub

1. Commit and push **all** changed files.
2. In Streamlit Community Cloud open the app.
3. Wait for the dependency rebuild to finish.
4. Open **Manage app → Cloud logs** and confirm the build completed.
5. Reboot the app once after the rebuild.
6. Test with a normal public YouTube video.

Do not just refresh the browser after changing `requirements.txt` or
`packages.txt`; dependency changes trigger a rebuild.

## What to look for in Cloud logs

A healthy startup should contain messages similar to:

```text
FFmpeg: /usr/bin/ffmpeg
YouTube browser for WPC: /usr/bin/chromium
Deno JS runtime: .../bin/deno
yt-dlp version: ...
```

When a download starts, yt-dlp verbose output should show a PO Token Provider
such as:

```text
[youtube] [pot] PO Token Providers: wpc-...
```

Do not expose PO tokens or cookies in the UI or GitHub.

## Optional server-side cookies

Only use this if YouTube still requires an authenticated session for a video.
Keep the cookies file private and inject the path through a server-side secret.
Never commit `cookies.txt` to GitHub.

```text
YOUTUBE_COOKIES_FILE=/absolute/path/to/cookies.txt
```

## Optional diagnostics

The backend exposes `get_youtube_runtime_diagnostics()` so the Streamlit UI
can safely display whether yt-dlp, Deno, Chromium, WPC and FFmpeg are present.
It does not display cookies or PO tokens.

## Important limitation

A PO-token provider does not guarantee every video will download. YouTube can
still reject a datacenter IP, account/session, geo-restricted video, age/
private/member-only video, or a particular media request. Current yt-dlp
releases and YouTube extractor behavior can change over time.


### Important Python API fix
The downloader configures yt-dlp JavaScript runtimes using the Python API shape `{"deno": {}}` or `{"deno": {"path": "/path/to/deno"}}`. A string value such as `{"deno": "/path/to/deno"}` causes yt-dlp to fail before extraction with `Invalid js_runtimes format`.

The WPC provider is configured with `youtubepot-wpc:browser_path=/usr/bin/chromium`, matching the provider's documented configuration.
