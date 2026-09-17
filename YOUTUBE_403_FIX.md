# YouTube 403 / "Sign in to confirm you're not a bot" fix

The old implementation forced the Android client and format `18`. That is
not a permanent workaround: YouTube can enforce Proof of Origin (PO) tokens
for Google Video Server requests and can also block a server IP/account.

This update changes the architecture:

- Current stable `yt-dlp` line.
- `yt-dlp[default]` so the matching EJS challenge-solver package is installed.
- Multiple current YouTube clients instead of hard-coded Android format 18.
- WebPoClient PO-token provider (`yt-dlp-getpot-wpc`) for automatic PO tokens
  when Chrome/Chromium is available.
- Optional server-side cookies through `YOUTUBE_COOKIES_FILE` or local
  `YOUTUBE_COOKIES_FROM_BROWSER`.
- Optional bgutil HTTP PO provider through `YOUTUBE_BGUTIL_URL`.
- One download pipeline is used by Shorts, MP3 and full-video downloads.
- Download output is verified before the UI reports success.

## What you must do after deployment

### Streamlit Cloud

1. Push the updated project.
2. Reboot/redeploy the app so the new `requirements.txt` and `packages.txt`
   are installed.
3. Test with a **public, non-age-restricted video** first.
4. If the server still receives a bot challenge, configure a fresh server-side
   cookies file or a reachable PO-token provider.

### Local Windows

```powershell
pip install -U -r requirements.txt
streamlit run app.py
```

If YouTube asks for authentication, a local browser-cookie test is supported:

```powershell
$env:YOUTUBE_COOKIES_FROM_BROWSER="chrome"
streamlit run app.py
```

Never commit browser cookies to GitHub.

## Why there is no fake "always works" fallback

YouTube's PO-token enforcement is changing. A client/format that works today
can be rejected later. The current yt-dlp documentation recommends a PO-token
provider rather than manually extracting a static token. A token can also be
bound to a video/session and may expire, so hard-coding one token is not a
reliable solution.
