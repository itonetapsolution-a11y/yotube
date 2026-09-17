"""YouTube download backend.

This module is deliberately kept separate from the Streamlit UI so every
YouTube feature uses the same download/authentication pipeline.

Current YouTube changes mean a plain yt-dlp request can receive
"Sign in to confirm you're not a bot" / HTTP 403.  The pipeline therefore:
  * uses current yt-dlp + JS runtime support;
  * can use the WebPoClient PO-token provider when installed;
  * optionally uses server-side cookies supplied through environment vars;
  * tries several supported YouTube clients instead of hard-coding Android;
  * verifies the output before returning success.

No cookies or PO tokens are sent to the Streamlit frontend.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable

import pysubs2
import yt_dlp

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [YTD] %(levelname)s %(message)s",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger("yt_downloader")

# -----------------------------------------------------------------------------
# FFmpeg
# -----------------------------------------------------------------------------
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception as exc:  # pragma: no cover - environment dependent
    log.info("static_ffmpeg unavailable: %s", exc)

FFMPEG_EXE = shutil.which("ffmpeg")
FFMPEG_DIR = os.path.dirname(FFMPEG_EXE) if FFMPEG_EXE else None
if FFMPEG_EXE:
    log.info("FFmpeg: %s", FFMPEG_EXE)
else:
    log.warning("FFmpeg was not found in PATH")

# WPC needs a real Chrome/Chromium executable. Streamlit Community Cloud
# installs Chromium via packages.txt; do not rely on nodriver guessing the path.
_BROWSER_CANDIDATES = (
    os.getenv("YOUTUBE_BROWSER_PATH", "").strip(),
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
)
BROWSER_EXE = next((p for p in _BROWSER_CANDIDATES if p and os.path.isfile(p)), None)
if BROWSER_EXE:
    log.info("YouTube browser for WPC: %s", BROWSER_EXE)
else:
    log.warning("No Chrome/Chromium executable found; WPC PO-token provider will be unavailable")

DENO_EXE = shutil.which("deno")
if DENO_EXE:
    log.info("Deno JS runtime: %s", DENO_EXE)
else:
    log.warning("Deno JS runtime was not found in PATH")

log.info("yt-dlp version: %s", getattr(yt_dlp.version, "__version__", "unknown"))

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _cookie_options() -> dict:
    """Return optional server-side cookie settings.

    YOUTUBE_COOKIES_FILE should point to a Netscape/Mozilla cookies.txt file.
    YOUTUBE_COOKIES_FROM_BROWSER may be e.g. 'chrome' or 'firefox' for local use.
    Never put either value in the Streamlit UI.
    """
    opts: dict = {}
    cookie_file = os.getenv("YOUTUBE_COOKIES_FILE", "").strip()
    browser = os.getenv("YOUTUBE_COOKIES_FROM_BROWSER", "").strip()

    if cookie_file and os.path.isfile(cookie_file):
        opts["cookiefile"] = cookie_file
        log.info("YouTube cookies: server-side cookie file enabled")
    elif browser:
        opts["cookiesfrombrowser"] = (browser, None, None, None)
        log.info("YouTube cookies: browser extraction enabled for %s", browser)
    return opts


def _provider_options() -> dict:
    """Configure PO-token providers explicitly.

    The WPC plugin is auto-discovered by yt-dlp when installed, but on
    Streamlit Community Cloud we explicitly pass the Chromium path so the
    provider does not depend on browser auto-discovery.
    """
    opts: dict = {}
    extractor_args: dict = {}

    if BROWSER_EXE:
        extractor_args["youtubepot-wpc"] = {"browser_path": [BROWSER_EXE]}
        log.info("YouTube PO provider: WPC enabled with browser=%s", BROWSER_EXE)
    else:
        log.warning("YouTube PO provider: WPC cannot start because Chromium is missing")

    bgurl = os.getenv("YOUTUBE_BGUTIL_URL", "").strip()
    if bgurl:
        extractor_args["youtubepot-bgutilhttp"] = {"base_url": [bgurl]}
        log.info("YouTube PO provider: bgutil HTTP %s", bgurl)

    if extractor_args:
        opts["extractor_args"] = extractor_args
    return opts


def _base_options() -> dict:
    opts = {
        "quiet": True,
        "no_warnings": False,
        "retries": 4,
        "fragment_retries": 3,
        "file_access_retries": 3,
        "socket_timeout": 30,
        "continuedl": True,
        "overwrites": True,
        "noprogress": True,
        "concurrent_fragment_downloads": 4,
        # Current yt-dlp uses EJS for YouTube JS challenges. The project
        # installs the official Deno binary + yt-dlp[default], so the bundled
        # EJS package can be used without downloading challenge code at runtime.
        # Python API format: runtime -> configuration dict.
        # Passing a string here causes yt-dlp to raise:
        # "Invalid js_runtimes format, expected a dict of {runtime: {config}}".
        "js_runtimes": {"deno": ({"path": DENO_EXE} if DENO_EXE else {})},
    }
    if FFMPEG_DIR:
        opts["ffmpeg_location"] = FFMPEG_DIR
    opts.update(_cookie_options())

    # If the external bgutil provider is configured, merge its extractor args.
    provider = _provider_options()
    if provider:
        opts = _merge_extractor_args(opts, provider)

    # Set YOUTUBE_POT_TRACE=1 only while debugging. Never log actual tokens.
    if _truthy("YOUTUBE_POT_TRACE"):
        opts = _merge_extractor_args(opts, {
            "extractor_args": {"youtube": {"pot_trace": ["true"]}}
        })
    return opts


def _client_args(client: str | None) -> dict:
    if not client:
        return {}
    return {"extractor_args": {"youtube": {"player_client": [client]}}}


def _merge_extractor_args(base: dict, extra: dict) -> dict:
    out = dict(base)
    ea = {k: dict(v) for k, v in out.get("extractor_args", {}).items()}
    for key, value in extra.get("extractor_args", {}).items():
        if key in ea:
            ea[key].update(value)
        else:
            ea[key] = dict(value)
    out["extractor_args"] = ea
    return out


def _ydl_options(client: str | None, fmt: str | None, outtmpl: str | None,
                 extra: dict | None = None) -> dict:
    opts = _base_options()
    opts = _merge_extractor_args(opts, _client_args(client))
    if fmt:
        opts["format"] = fmt
    if outtmpl:
        opts["outtmpl"] = outtmpl
    if extra:
        # extractor_args needs a deep-ish merge; everything else can overwrite.
        opts = _merge_extractor_args(opts, extra)
        for k, v in extra.items():
            if k != "extractor_args":
                opts[k] = v
    return opts


# Order matters: current yt-dlp recommends using supported clients rather than
# assuming the old Android format 18 path is permanently available.
_CLIENT_CHAIN: tuple[str | None, ...] = (
    "mweb",         # works with WPC PO-token provider when installed
    "web_safari",   # can expose HLS formats that don't need GVS PO token
    "web_embedded", # public embeddable videos
    "android_vr",   # useful fallback for public videos
    None,            # yt-dlp's current default client set
)


def _is_http_or_bot_error(message: str) -> bool:
    low = message.lower()
    needles = (
        "http error 403", "403 forbidden", "http error 429", "too many requests",
        "sign in to confirm", "not a bot", "po token", "botguard",
        "unable to download api page", "forbidden",
    )
    return any(n in low for n in needles)


def _find_media(directory: str, extensions: Iterable[str]) -> str | None:
    wanted = tuple(x.lower() for x in extensions)
    candidates: list[str] = []
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isfile(path) and name.lower().endswith(wanted):
            candidates.append(path)
    if not candidates:
        return None
    return sorted(candidates, key=lambda p: os.path.getmtime(p), reverse=True)[0]


def _verify(path: str, label: str) -> str:
    if not path or not os.path.isfile(path):
        raise RuntimeError(f"{label} download completed without creating a file.")
    size = os.path.getsize(path)
    if size <= 0:
        raise RuntimeError(f"The downloaded {label} file is empty.")
    log.info("Verified %s: %s (%.1f MB)", label, path, size / 1048576)
    return path


def _run_download(
    url: str,
    outtmpl: str,
    fmt: str,
    merge_fmt: str = "mp4",
    extra: dict | None = None,
) -> None:
    """Download with supported-client fallback.

    A 403/bot response is retried with another client. We do not claim that a
    particular client is permanently 403-proof; YouTube changes enforcement.
    """
    last_error: Exception | None = None

    for client in _CLIENT_CHAIN:
        opts = _ydl_options(client, fmt, outtmpl, extra)
        opts["merge_output_format"] = merge_fmt
        label = client or "default"
        log.info("[TRY] YouTube client=%s format=%s", label, fmt)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            log.info("[OK] YouTube download client=%s", label)
            return
        except Exception as exc:
            last_error = exc
            msg = str(exc)
            log.warning("[FAIL] client=%s: %s", label, msg[:500])
            if _is_http_or_bot_error(msg):
                continue
            raise RuntimeError(
                f"YouTube download failed: {msg[:500]}"
            ) from exc

    provider_hint = (
        " The server needs a current PO-token provider or valid server-side "
        "YouTube cookies."
    )
    raise RuntimeError(
        "YouTube rejected all available media requests with a 403/bot check."
        + provider_hint
        + " See the deployment guide included with this project."
    ) from last_error


# -----------------------------------------------------------------------------
# Diagnostics
# -----------------------------------------------------------------------------

def get_youtube_runtime_diagnostics() -> dict:
    """Return safe deployment diagnostics for the Streamlit UI."""
    provider_installed = False
    provider_version = None
    try:
        import importlib.metadata as metadata
        provider_version = metadata.version("yt-dlp-getpot-wpc")
        provider_installed = True
    except Exception:
        pass

    return {
        "yt_dlp": getattr(yt_dlp.version, "__version__", "unknown"),
        "deno": bool(DENO_EXE),
        "deno_path": DENO_EXE or "not found",
        "chromium": bool(BROWSER_EXE),
        "chromium_path": BROWSER_EXE or "not found",
        "wpc_package": provider_installed,
        "wpc_version": provider_version or "not installed",
        "ffmpeg": bool(FFMPEG_EXE),
        "cookies_configured": bool(os.getenv("YOUTUBE_COOKIES_FILE", "").strip()),
    }


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def get_video_info(url: str) -> dict:
    """Fetch metadata without downloading media."""
    last: Exception | None = None
    for client in _CLIENT_CHAIN:
        try:
            opts = _ydl_options(client, None, None)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url.strip(), download=False)
            return {
                "id": info.get("id"),
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "uploader": info.get("uploader"),
            }
        except Exception as exc:
            last = exc
            if not _is_http_or_bot_error(str(exc)):
                break
    raise RuntimeError(f"Could not fetch YouTube information: {last}") from last


def download_video_and_subtitles(url: str, output_dir: str,
                                 format_selector: str | None = None) -> tuple[str, str | None]:
    """Download the source video and optionally English subtitles."""
    os.makedirs(output_dir, exist_ok=True)
    outtmpl = os.path.join(output_dir, "input_video.%(ext)s")
    fmt = format_selector or (
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    )

    _run_download(url.strip(), outtmpl, fmt, "mp4")
    video = _find_media(output_dir, (".mp4", ".mkv", ".webm", ".mov"))
    if not video:
        raise RuntimeError("YouTube reported a successful download, but no video file was created.")
    _verify(video, "video")

    subtitle: str | None = None
    try:
        sub_opts = _ydl_options(
            "mweb", None, outtmpl,
            {
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en", "en-orig"],
                "subtitlesformat": "srt/vtt/best",
                "ignoreerrors": True,
            },
        )
        with yt_dlp.YoutubeDL(sub_opts) as ydl:
            ydl.download([url.strip()])
    except Exception as exc:
        log.warning("Subtitle download failed (non-fatal): %s", exc)

    subtitle = _find_media(output_dir, (".srt",))
    if not subtitle:
        vtt = _find_media(output_dir, (".vtt",))
        if vtt:
            subtitle = convert_vtt_to_srt(vtt)
    return video, subtitle


def download_video(url: str, output_dir: str, container: str = "mp4",
                    format_selector: str | None = None) -> str:
    os.makedirs(output_dir, exist_ok=True)
    outtmpl = os.path.join(output_dir, "video_out.%(ext)s")
    fmt = format_selector or "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    _run_download(url.strip(), outtmpl, fmt, container)
    path = _find_media(output_dir, (f".{container}", ".mp4", ".mkv", ".webm"))
    return _verify(path, "video") if path else _verify("", "video")


def download_audio(url: str, output_dir: str, codec: str = "mp3", bitrate: str = "192") -> str:
    os.makedirs(output_dir, exist_ok=True)
    outtmpl = os.path.join(output_dir, "audio_out.%(ext)s")
    _run_download(
        url.strip(), outtmpl,
        "bestaudio[ext=m4a]/bestaudio/best",
        "mp4",
        {
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
                "preferredquality": bitrate,
            }]
        },
    )
    path = _find_media(output_dir, (f".{codec}", ".mp3", ".m4a", ".wav", ".aac", ".ogg"))
    return _verify(path, "audio") if path else _verify("", "audio")


def convert_vtt_to_srt(vtt_path: str) -> str | None:
    if not vtt_path or not os.path.exists(vtt_path):
        return None
    if vtt_path.lower().endswith(".srt"):
        return vtt_path
    srt_path = os.path.splitext(vtt_path)[0] + ".srt"
    try:
        pysubs2.load(vtt_path).save(srt_path)
        return srt_path
    except Exception as exc:
        log.warning("VTT→SRT failed: %s", exc)
        return None
