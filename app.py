import os
import shutil
import zipfile
import tempfile

# Safe FFmpeg Init: On Streamlit Cloud / Linux, system FFmpeg is installed via packages.txt.
# On Windows, fall back to static_ffmpeg if ffmpeg is not already in PATH.
# IMPORTANT: Call add_paths() FIRST so shutil.which can find the bundled ffmpeg.
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

FFMPEG_DIR = None
if shutil.which('ffmpeg'):
    FFMPEG_DIR = os.path.dirname(shutil.which('ffmpeg'))

import yt_dlp
import streamlit as st
from downloader import (
    get_video_info, download_video_and_subtitles, download_audio, download_video
)
from processor import generate_all_shorts

st.set_page_config(
    page_title="YouTube & All-in-One Studio Suite",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────────────────────
#  THEME TOGGLE STATE & LOGIC
# ─────────────────────────────────────────────────────────────────────────────
if 'theme_mode' not in st.session_state:
    st.session_state['theme_mode'] = 'Dark Mode'

if st.session_state['theme_mode'] == 'Dark Mode':
    THEME_CSS = """
    :root {
        --yt-red:        #FF0000;
        --yt-red-hover:  #CC0000;
        --yt-bg:         #0f0f0f;
        --yt-surf:       #1f1f1f;
        --yt-surf2:      #272727;
        --yt-surf3:      #383838;
        --yt-border:     #3f3f3f;
        --yt-text:       #f1f1f1;
        --yt-muted:      #aaaaaa;
        --yt-subtle:     #717171;
        --yt-navbar:     #212121;
        --yt-input-bg:   #272727;
    }
    """
else:
    THEME_CSS = """
    :root {
        --yt-red:        #FF0000;
        --yt-red-hover:  #CC0000;
        --yt-bg:         #f9f9f9;
        --yt-surf:       #ffffff;
        --yt-surf2:      #f2f2f2;
        --yt-surf3:      #e5e5e5;
        --yt-border:     #e0e0e0;
        --yt-text:       #0f0f0f;
        --yt-muted:      #606060;
        --yt-subtle:     #909090;
        --yt-navbar:     #ffffff;
        --yt-input-bg:   #ffffff;
    }
    """

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

{THEME_CSS}

html, body, .stApp, [data-testid="stAppViewContainer"] {{
    background-color: var(--yt-bg) !important;
    color: var(--yt-text) !important;
    font-family: 'Roboto', sans-serif !important;
}}
[data-testid="stHeader"]  {{ background: transparent !important; }}
[data-testid="stSidebar"] {{ display: none !important; }}
section.main > div        {{ padding-top: 0 !important; }}
#MainMenu, footer, [data-testid="stToolbar"] {{ display: none !important; }}

.yt-topbar {{
    background: var(--yt-navbar);
    border-bottom: 1px solid var(--yt-border);
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 999;
    margin: -1rem -1rem 1rem -1rem;
}}
.yt-logo-wrap {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.yt-logo-box {{
    background: #FF0000;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 16px;
    font-weight: 900;
    color: #fff;
}}
.yt-logo-name {{
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--yt-text);
}}
.yt-logo-sub {{
    font-size: 0.72rem;
    color: var(--yt-muted);
    border: 1px solid var(--yt-border);
    border-radius: 4px;
    padding: 2px 7px;
    font-weight: 500;
}}

.stTabs [data-baseweb="tab-list"] {{
    background: var(--yt-navbar) !important;
    border-bottom: 1px solid var(--yt-border) !important;
    gap: 4px !important;
    padding: 0 10px !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--yt-muted) !important;
    font-family: 'Roboto', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 12px 18px !important;
    border-bottom: 2px solid transparent !important;
}}
.stTabs [aria-selected="true"] {{
    color: var(--yt-red) !important;
    border-bottom: 2px solid var(--yt-red) !important;
    font-weight: 700 !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: var(--yt-text) !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 20px !important;
    background: var(--yt-bg) !important;
}}

.yt-card {{
    background: var(--yt-surf);
    border: 1px solid var(--yt-border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}
.yt-card2 {{
    background: var(--yt-surf2);
    border: 1px solid var(--yt-border);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
}}
.yt-card3 {{
    background: var(--yt-surf3);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
}}

.yt-sec-title {{
    font-size: 1.05rem;
    font-weight: 500;
    color: var(--yt-text);
    margin-bottom: 8px;
}}
.yt-chip {{
    display: inline-block;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 10px;
}}
.chip-red    {{ background: rgba(255,0,0,.15);    color: #FF6B6B; border: 1px solid rgba(255,0,0,.3); }}
.chip-blue   {{ background: rgba(6,95,212,.15);   color: #60a5fa; border: 1px solid rgba(6,95,212,.3); }}
.chip-green  {{ background: rgba(43,166,64,.15);  color: #4ade80; border: 1px solid rgba(43,166,64,.3); }}
.chip-orange {{ background: rgba(242,153,0,.15);  color: #fbbf24; border: 1px solid rgba(242,153,0,.3); }}
.chip-purple {{ background: rgba(123,47,190,.15); color: #c084fc; border: 1px solid rgba(123,47,190,.3); }}

.stTextInput input {{
    background: var(--yt-input-bg) !important;
    border: 1px solid var(--yt-border) !important;
    border-radius: 24px !important;
    color: var(--yt-text) !important;
    padding: 10px 18px !important;
}}
.stSelectbox > div > div {{
    background: var(--yt-input-bg) !important;
    border: 1px solid var(--yt-border) !important;
    border-radius: 8px !important;
    color: var(--yt-text) !important;
}}

.stButton > button {{
    background: var(--yt-surf2) !important;
    color: var(--yt-text) !important;
    border: 1px solid var(--yt-border) !important;
    border-radius: 20px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
}}
.stButton > button[kind="primary"] {{
    background: var(--yt-red) !important;
    border-color: var(--yt-red) !important;
    color: #fff !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: var(--yt-red-hover) !important;
}}

.stDownloadButton > button {{
    background: #FF0000 !important;
    border: 1px solid #FF0000 !important;
    color: #ffffff !important;
    border-radius: 6px !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    padding: 10px 20px !important;
    width: 100% !important;
    box-shadow: 0 2px 6px rgba(255,0,0,0.3) !important;
}}
.stDownloadButton > button:hover {{
    background: #CC0000 !important;
}}

.result-row {{
    display: flex;
    align-items: center;
    background: var(--yt-surf2);
    border: 1px solid var(--yt-border);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}}
.result-icon {{ font-size: 1.8rem; margin-right: 14px; }}
.result-name {{ font-size: 0.95rem; font-weight: 500; color: var(--yt-text); }}
.result-sub  {{ font-size: 0.8rem; color: var(--yt-muted); margin-top: 3px; }}

.vid-row {{ display: flex; gap: 14px; align-items: flex-start; }}
.vid-thumb {{ width: 150px; border-radius: 8px; flex-shrink: 0; }}
.vid-title {{ font-size: 0.95rem; font-weight: 500; color: var(--yt-text); line-height: 1.4; margin-bottom: 6px; }}
.vid-meta  {{ font-size: 0.8rem; color: var(--yt-muted); margin-top: 3px; }}
.vid-badge {{ background: #FF0000; color: #fff; font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; display: inline-block; margin-top: 8px; }}

hr {{ border-color: var(--yt-border) !important; margin: 16px 0 !important; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  TOPBAR & THEME SWITCHER
# ─────────────────────────────────────────────────────────────────────────────
nav_c1, nav_c2 = st.columns([4, 1])
with nav_c1:
    st.markdown("""
    <div class="yt-logo-wrap">
        <div class="yt-logo-box">▶</div>
        <span class="yt-logo-name">YouTube Studio</span>
        <span class="yt-logo-sub">Suite Pro</span>
    </div>
    """, unsafe_allow_html=True)

with nav_c2:
    selected_theme = st.selectbox(
        "Theme",
        options=["Dark Mode 🌙", "Light Mode ☀️"],
        index=0 if st.session_state['theme_mode'] == 'Dark Mode' else 1,
        label_visibility="collapsed"
    )
    new_mode = "Dark Mode" if "Dark" in selected_theme else "Light Mode"
    if new_mode != st.session_state['theme_mode']:
        st.session_state['theme_mode'] = new_mode
        st.rerun()

WORK_DIR = os.path.join(tempfile.gettempdir(), 'all_media_suite')
os.makedirs(WORK_DIR, exist_ok=True)

def _ydl_base():
    """Legacy-compatible base options for non-YouTube tabs.

    YouTube download operations use downloader.py so PO-token/cookie/client
    handling is centralized.
    """
    opts = {"quiet": True, "no_warnings": True}
    if FFMPEG_DIR:
        opts["ffmpeg_location"] = FFMPEG_DIR
    return opts

def fetch_info(url):
    clean_url = url.strip()
    try:
        return get_video_info(clean_url)
    except Exception as yt_err:
        import re, requests
        m = re.search(r'(?:v=|\/|youtu\.be\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})', clean_url)
        if m:
            vid = m.group(1)
            try:
                ores = requests.get(f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json', timeout=5)
                if ores.status_code == 200:
                    data = ores.json()
                    return {
                        'id': vid,
                        'title': data.get('title', 'YouTube Video'),
                        'uploader': data.get('author_name', 'YouTube Creator'),
                        'thumbnail': f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg',
                        'duration': 0,
                        'is_fallback': True
                    }
            except Exception:
                pass
        raise yt_err

def video_info_card(info):
    thumb   = info.get('thumbnail', '')
    title   = info.get('title', 'Unknown')
    channel = info.get('uploader') or info.get('channel') or 'Unknown'
    dur     = int(info.get('duration', 0))
    st.markdown(f"""
    <div class="yt-card2">
        <div class="vid-row">
            {'<img class="vid-thumb" src="' + thumb + '" />' if thumb else '<div style="width:80px;height:80px;background:#333;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:2rem;">🎬</div>'}
            <div>
                <div class="vid-title">{title}</div>
                <div class="vid-meta">📺 {channel}</div>
                {f'<div class="vid-meta">⏱️ {dur//60}m {dur%60}s</div>' if dur else ''}
                <span class="vid-badge">✓ READY</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  APP TABS (ALL 6 ORIGINAL TOOLS)
# ─────────────────────────────────────────────────────────────────────────────
tab_shorts, tab_mp3, tab_video, tab_insta, tab_pin, tab_universal = st.tabs([
    "✂️ Shorts Generator",
    "🎵 YouTube → MP3",
    "📥 YouTube Video",
    "📸 Instagram",
    "📌 Pinterest",
    "🌐 Universal (FB / X / TikTok / Reddit)"
])

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 1: SHORTS GENERATOR
# ═════════════════════════════════════════════════════════════════════════════
with tab_shorts:
    st.markdown('<span class="yt-chip chip-red">Shorts Generator</span>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sec-title">Convert full YouTube videos into 9:16 Shorts, Reels or Landscape clips with song title banner & subtitles</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        url_s = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...", key="url_s", label_visibility="collapsed")
        st.caption("Paste YouTube video link above")
        
        fc1, _ = st.columns([1, 3])
        with fc1:
            if st.button("🔍 Fetch Info", key="f_s"):
                if url_s.strip():
                    with st.spinner("Fetching video info..."):
                        try:
                            st.session_state['s_info'] = fetch_info(url_s.strip())
                        except Exception as e:
                            st.error(str(e))

        if 's_info' in st.session_state:
            video_info_card(st.session_state['s_info'])

        st.markdown("<br>", unsafe_allow_html=True)
        gen_s_btn = st.button("▶  GENERATE SHORTS CLIPS", type="primary", use_container_width=True, key="btn_s") if url_s.strip() else False

    with c2:
        st.markdown('<div class="yt-card">', unsafe_allow_html=True)
        st.markdown('<span class="yt-chip chip-blue">Shorts Settings</span>', unsafe_allow_html=True)
        
        ar_lbl = st.selectbox("📐 Aspect Ratio", [
            "📱 9:16 — Shorts / Reels / TikTok",
            "📺 16:9 — Landscape (Standard)",
            "🔲 1:1 — Square (Instagram)",
            "📸 4:5 — Portrait (Feed Post)"
        ], key="ar_s")
        ar_val = {"📱 9:16 — Shorts / Reels / TikTok":"9:16","📺 16:9 — Landscape (Standard)":"16:9","🔲 1:1 — Square (Instagram)":"1:1","📸 4:5 — Portrait (Feed Post)":"4:5"}[ar_lbl]
        
        bg_lbl = st.selectbox("🎬 Background Style", ["Blur Background (Recommended)", "Center Crop", "Black Padding"], key="bg_s")
        bg_val = {"Blur Background (Recommended)":"blur", "Center Crop":"crop", "Black Padding":"fit"}[bg_lbl]
        
        st.markdown("---")
        sc1, sc2 = st.columns(2)
        dur_s = sc1.slider("Clip Length (sec)", 10, 60, 30, 5, key="dur_s")
        max_s = sc2.slider("Max Clips", 1, 10, 5, key="max_s")
        
        st.markdown("---")
        wm_en = st.checkbox("🎵 Add Song Title Banner", value=True, key="wm_s")
        def_t = st.session_state.get('s_info', {}).get('title', '') if 's_info' in st.session_state else ''
        wm_t  = st.text_input("Banner Text", value=def_t, key="wmt_s")
        
        wc1, wc2 = st.columns(2)
        pos_s = wc1.selectbox("Position", ["Top", "Bottom", "Center"], key="pos_s").lower()
        sty_lbl = wc2.selectbox("Style", ["🌟 Yellow Box", "💎 Neon Cyan", "🔥 Red Badge", "⚪ White Shadow"], key="sty_s")
        sty_s = {"🌟 Yellow Box":"yellow_box", "💎 Neon Cyan":"neon_cyan", "🔥 Red Badge":"red_badge", "⚪ White Shadow":"white_shadow"}[sty_lbl]
        
        st.markdown("---")
        sub_s = st.checkbox("📝 Burn Auto-Subtitles", value=True, key="sub_s")
        st.markdown('</div>', unsafe_allow_html=True)

    if gen_s_btn and url_s.strip():
        st.markdown("---")
        pb1 = st.progress(0); stxt1 = st.empty()
        sdir = os.path.join(WORK_DIR, "shorts_run")
        shutil.rmtree(sdir, ignore_errors=True)
        os.makedirs(sdir, exist_ok=True)
        try:
            stxt1.markdown("⬇️ **Downloading video stream...**"); pb1.progress(15)
            vf, sf = download_video_and_subtitles(url_s.strip(), sdir)
            if not sub_s: sf = None
            stxt1.markdown(f"✂️ **Generating {ar_val} Clips with {sty_lbl}...**"); pb1.progress(35)
            def _up(cur, tot, m): pb1.progress(35 + int((cur/tot)*60)); stxt1.markdown(f"✂️ **{m}**")
            clips = generate_all_shorts(
                vf, os.path.join(sdir,"clips"), dur_s, max_s, ar_val, bg_val,
                wm_t if wm_en else None, pos_s, sty_s, sf, _up
            )
            pb1.progress(100); stxt1.markdown("✅ **Shorts clips generated successfully!**")
            st.session_state['gen_clips'] = clips
            st.session_state['gen_dir']   = sdir
        except Exception as e:
            st.error(f"❌ {e}"); pb1.empty(); stxt1.empty()

    if st.session_state.get('gen_clips'):
        clips = st.session_state['gen_clips']
        sdir  = st.session_state['gen_dir']
        st.markdown("---")
        st.markdown(f'<div class="yt-sec-title">🎉 {len(clips)} Clips Ready for Download</div>', unsafe_allow_html=True)
        
        zp = os.path.join(sdir, "shorts_collection.zip")
        with zipfile.ZipFile(zp, 'w') as zf:
            for c in clips: zf.write(c, os.path.basename(c))
        with open(zp, "rb") as fz:
            zip_data = fz.read()
        st.download_button("📦 Download All Shorts as ZIP", zip_data, "shorts_collection.zip", "application/zip", use_container_width=True)

        cols = st.columns(min(len(clips), 3))
        for idx, cp in enumerate(clips):
            with cols[idx % len(cols)]:
                st.video(cp)
                with open(cp, "rb") as cf:
                    clip_data = cf.read()
                st.download_button(f"⬇ Download Short #{idx+1}", clip_data, os.path.basename(cp), "video/mp4", key=f"dl_s_{idx}", use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 2: YOUTUBE TO MP3
# ═════════════════════════════════════════════════════════════════════════════
with tab_mp3:
    st.markdown('<span class="yt-chip chip-green">YouTube → MP3</span>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sec-title">Extract high-quality MP3 / M4A audio with album art and metadata</div>', unsafe_allow_html=True)

    m1, m2 = st.columns([3, 2], gap="large")
    with m1:
        url_m = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...", key="url_m", label_visibility="collapsed")
        st.caption("Paste YouTube music or video link above")
        
        fcm, _ = st.columns([1, 3])
        with fcm:
            if st.button("🔍 Fetch Info", key="f_m"):
                if url_m.strip():
                    with st.spinner("Fetching..."):
                        try: st.session_state['m_info'] = fetch_info(url_m.strip())
                        except Exception as e: st.error(str(e))

        if 'm_info' in st.session_state:
            video_info_card(st.session_state['m_info'])

        st.markdown("<br>", unsafe_allow_html=True)
        dl_m_btn = st.button("🎵 EXTRACT AUDIO (MP3)", type="primary", use_container_width=True, key="btn_m") if url_m.strip() else False

    with m2:
        st.markdown('<div class="yt-card">', unsafe_allow_html=True)
        st.markdown('<span class="yt-chip chip-green">Audio Quality</span>', unsafe_allow_html=True)
        q_m = st.selectbox("Bitrate", ["320 kbps (Studio Quality)", "256 kbps (High Quality)", "192 kbps (Standard)", "128 kbps (Compact)"], key="qm")
        br_m = q_m.split()[0]
        fmt_m = st.selectbox("Format", ["MP3", "M4A", "WAV"], key="fmtm").lower()
        meta_m = st.checkbox("Embed Album Art & Title Tag", value=True, key="metam")
        st.markdown('</div>', unsafe_allow_html=True)

    if dl_m_btn and url_m.strip():
        st.markdown("---")
        pb2 = st.progress(0); stxt2 = st.empty()
        mdir = os.path.join(WORK_DIR, "mp3_run")
        shutil.rmtree(mdir, ignore_errors=True)
        os.makedirs(mdir, exist_ok=True)
        try:
            stxt2.markdown("🎵 **Extracting audio stream...**"); pb2.progress(20)
            afile = download_audio(url_m.strip(), mdir, codec=fmt_m, bitrate=br_m)
            pb2.progress(90)

            if afile and os.path.exists(afile):
                pb2.progress(100); stxt2.markdown("✅ **Audio ready!**")
                fsize = os.path.getsize(afile) / (1024*1024)
                st.markdown(f'<div class="result-row"><span class="result-icon">🎵</span><div><div class="result-name">{os.path.basename(afile)}</div><div class="result-sub">{fmt_m.upper()} · {br_m}kbps · {fsize:.1f} MB</div></div></div>', unsafe_allow_html=True)
                with open(afile, "rb") as af:
                    audio_data = af.read()
                st.download_button(f"⬇ Download {fmt_m.upper()}", audio_data, os.path.basename(afile), f"audio/{fmt_m}", use_container_width=True)
            else:
                st.error("Audio extraction failed. Please try again.")
        except Exception as e:
            st.error(f"❌ {e}"); pb2.empty(); stxt2.empty()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 3: YOUTUBE VIDEO DOWNLOADER
# ═════════════════════════════════════════════════════════════════════════════
with tab_video:
    st.markdown('<span class="yt-chip chip-orange">Video Downloader</span>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sec-title">Download full YouTube videos in 4K, 1080p, 720p or 480p</div>', unsafe_allow_html=True)

    v1, v2 = st.columns([3, 2], gap="large")
    with v1:
        url_v = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...", key="url_v", label_visibility="collapsed")
        st.caption("Paste YouTube video link above")
        
        fcv, _ = st.columns([1, 3])
        with fcv:
            if st.button("🔍 Fetch Info", key="f_v"):
                if url_v.strip():
                    with st.spinner("Fetching..."):
                        try: st.session_state['v_info'] = fetch_info(url_v.strip())
                        except Exception as e: st.error(str(e))

        if 'v_info' in st.session_state:
            video_info_card(st.session_state['v_info'])

        st.markdown("<br>", unsafe_allow_html=True)
        dl_v_btn = st.button("📥 DOWNLOAD FULL VIDEO", type="primary", use_container_width=True, key="btn_v") if url_v.strip() else False

    with v2:
        st.markdown('<div class="yt-card">', unsafe_allow_html=True)
        st.markdown('<span class="yt-chip chip-orange">Quality Settings</span>', unsafe_allow_html=True)
        vq_lbl = st.selectbox("Resolution", [
            "🏆 Best Available (Highest Quality)",
            "4K — 2160p (Ultra HD)",
            "Full HD — 1080p",
            "HD — 720p",
            "SD — 480p"
        ], key="vql")
        vq_map = {
            "🏆 Best Available (Highest Quality)": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/18/best",
            "4K — 2160p (Ultra HD)": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160][ext=mp4]/18/best",
            "Full HD — 1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/18/best",
            "HD — 720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/18/best",
            "SD — 480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/18/best"
        }
        fmt_v = vq_map[vq_lbl]
        cont_v = st.selectbox("Container", ["MP4", "MKV"], key="contv").lower()
        sub_v  = st.checkbox("Download Subtitles (.srt)", value=False, key="subv")
        th_v   = st.checkbox("Download Thumbnail (.jpg)", value=False, key="thv")
        st.markdown('</div>', unsafe_allow_html=True)

    if dl_v_btn and url_v.strip():
        st.markdown("---")
        pb3 = st.progress(0); stxt3 = st.empty()
        vdir = os.path.join(WORK_DIR, "video_run")
        shutil.rmtree(vdir, ignore_errors=True)
        os.makedirs(vdir, exist_ok=True)
        try:
            stxt3.markdown("📥 **Downloading video stream...**"); pb3.progress(20)
            # Use the centralized YouTube downloader. This applies the same
            # PO-token/cookie/client fallback used by the Shorts generator.
            vfmt = fmt_v
            vfile = download_video(url_v.strip(), vdir, container=cont_v, format_selector=vfmt)

            if sub_v:
                try:
                    sub_opts_v = {
                        'skip_download': True,
                        'writesubtitles': True, 'writeautomaticsub': True,
                        'subtitleslangs': ['en', 'en-orig'],
                        'subtitlesformat': 'srt/vtt/best',
                        'outtmpl': os.path.join(vdir, 'video_out.%(ext)s'),
                        'ignoreerrors': True,
                    }
                    # Subtitle-only extraction is intentionally best-effort.
                    with yt_dlp.YoutubeDL(_ydl_base() | sub_opts_v) as ydl:
                        ydl.download([url_v.strip()])
                except Exception:
                    pass

            if th_v:
                try:
                    thumb_opts = _ydl_base() | {
                        'skip_download': True,
                        'writethumbnail': True,
                        'outtmpl': os.path.join(vdir, 'video_out.%(ext)s'),
                        'ignoreerrors': True,
                    }
                    with yt_dlp.YoutubeDL(thumb_opts) as ydl:
                        ydl.download([url_v.strip()])
                except Exception:
                    pass

            pb3.progress(90)

            if vfile and os.path.exists(vfile):
                pb3.progress(100); stxt3.markdown("✅ **Video ready for download!**")
                fsize = os.path.getsize(vfile) / (1024*1024)
                st.markdown(f'<div class="result-row"><span class="result-icon">🎬</span><div><div class="result-name">{os.path.basename(vfile)[:65]}</div><div class="result-sub">{cont_v.upper()} · {fsize:.1f} MB</div></div></div>', unsafe_allow_html=True)
                with open(vfile, "rb") as vf_d:
                    video_data = vf_d.read()
                st.download_button("⬇ Download Video File", video_data, os.path.basename(vfile), "video/mp4", use_container_width=True)

                # Show subtitle files if downloaded
                for f in os.listdir(vdir):
                    if f.endswith(('.srt', '.vtt')):
                        sub_path = os.path.join(vdir, f)
                        with open(sub_path, "rb") as sf: sub_data = sf.read()
                        st.download_button(f"⬇ Download Subtitle ({f})", sub_data, f, use_container_width=True)
            else:
                st.error("Video download failed.")
        except Exception as e:
            st.error(f"❌ {e}"); pb3.empty(); stxt3.empty()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 4: INSTAGRAM DOWNLOADER
# ═════════════════════════════════════════════════════════════════════════════
with tab_insta:
    st.markdown('<span class="yt-chip chip-purple">Instagram Downloader</span>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sec-title">Download Reels, Posts, Photos, Multi-Item Carousels & MP3 audio</div>', unsafe_allow_html=True)

    i1, i2 = st.columns([3, 2], gap="large")
    with i1:
        url_i = st.text_input("Instagram URL", placeholder="https://www.instagram.com/reel/... or /p/...", key="url_i", label_visibility="collapsed")
        st.caption("Paste public Instagram Reel or Post link above")
        
        fci, _ = st.columns([1, 3])
        with fci:
            if st.button("🔍 Fetch Info", key="f_i"):
                if url_i.strip():
                    with st.spinner("Fetching Instagram post..."):
                        try: st.session_state['i_info'] = fetch_info(url_i.strip())
                        except Exception as e: st.error(str(e))

        if 'i_info' in st.session_state:
            video_info_card(st.session_state['i_info'])

        st.markdown("<br>", unsafe_allow_html=True)
        dl_i_btn = st.button("📸 DOWNLOAD FROM INSTAGRAM", type="primary", use_container_width=True, key="btn_i") if url_i.strip() else False

    with i2:
        st.markdown('<div class="yt-card">', unsafe_allow_html=True)
        st.markdown('<span class="yt-chip chip-purple">Content Type</span>', unsafe_allow_html=True)
        ig_type = st.selectbox("Download As", ["🎬 Video / Reel (MP4)", "🎵 Audio Only (MP3)", "📸 Photo / Thumbnail (JPG)", "📦 Carousel ZIP (All Items)"], key="igt")
        st.markdown('</div>', unsafe_allow_html=True)

    if dl_i_btn and url_i.strip():
        st.markdown("---")
        pb4 = st.progress(0); stxt4 = st.empty()
        idir = os.path.join(WORK_DIR, "insta_run")
        shutil.rmtree(idir, ignore_errors=True); os.makedirs(idir, exist_ok=True)
        try:
            stxt4.markdown("📸 **Downloading from Instagram...**"); pb4.progress(25)
            yopts_i = _ydl_base()
            yopts_i.update({'outtmpl': os.path.join(idir, '%(id)s.%(ext)s'), 'ignoreerrors': True})
            if "MP3" in ig_type:
                yopts_i['format'] = 'bestaudio/best'
                yopts_i['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
            elif "Photo" in ig_type:
                yopts_i['writethumbnail'] = True; yopts_i['skip_download'] = True
            else:
                yopts_i['format'] = 'bestvideo+bestaudio/best'; yopts_i['merge_output_format'] = 'mp4'

            with yt_dlp.YoutubeDL(yopts_i) as ydl: ydl.download([url_i.strip()])
            pb4.progress(90)
            
            files = [os.path.join(idir, f) for f in sorted(os.listdir(idir)) if os.path.isfile(os.path.join(idir, f))]
            if not files:
                st.error("No files downloaded. The account or post may be private.")
            else:
                pb4.progress(100); stxt4.markdown(f"✅ **Downloaded {len(files)} file(s)!**")
                if len(files) > 2 or "Carousel" in ig_type:
                    zp_i = os.path.join(idir, "instagram_carousel.zip")
                    with zipfile.ZipFile(zp_i, 'w') as zf:
                        for fp in files: zf.write(fp, os.path.basename(fp))
                    with open(zp_i, "rb") as zfd:
                        c_data = zfd.read()
                    st.download_button("📦 Download Carousel as ZIP", c_data, "instagram_carousel.zip", "application/zip", use_container_width=True)
                else:
                    for fp in files:
                        fn = os.path.basename(fp); fs = os.path.getsize(fp)/(1024*1024); ext = fn.rsplit('.', 1)[-1].lower()
                        ico = "🎵" if ext in ('mp3', 'm4a') else ("🖼️" if ext in ('jpg', 'jpeg', 'png', 'webp') else "🎬")
                        st.markdown(f'<div class="result-row"><span class="result-icon">{ico}</span><div><div class="result-name">{fn}</div><div class="result-sub">{ext.upper()} · {fs:.1f} MB</div></div></div>', unsafe_allow_html=True)
                        with open(fp, "rb") as fd:
                            f_data = fd.read()
                        st.download_button(f"⬇ Download {fn[:45]}", f_data, fn, use_container_width=True)
        except Exception as e:
            st.error(f"❌ {e}"); pb4.empty(); stxt4.empty()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 5: PINTEREST DOWNLOADER
# ═════════════════════════════════════════════════════════════════════════════
with tab_pin:
    st.markdown('<span class="yt-chip chip-red">Pinterest Downloader</span>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sec-title">Download Pinterest Videos, GIFs, HD Images or complete Boards</div>', unsafe_allow_html=True)

    p1, p2 = st.columns([3, 2], gap="large")
    with p1:
        url_p = st.text_input("Pinterest URL", placeholder="https://www.pinterest.com/pin/...", key="url_p", label_visibility="collapsed")
        st.caption("Paste Pinterest Pin or Board URL above")
        
        fcp, _ = st.columns([1, 3])
        with fcp:
            if st.button("🔍 Fetch Info", key="f_p"):
                if url_p.strip():
                    with st.spinner("Fetching Pin info..."):
                        try: st.session_state['p_info'] = fetch_info(url_p.strip())
                        except Exception as e: st.error(str(e))

        if 'p_info' in st.session_state:
            video_info_card(st.session_state['p_info'])

        st.markdown("<br>", unsafe_allow_html=True)
        dl_p_btn = st.button("📌 DOWNLOAD FROM PINTEREST", type="primary", use_container_width=True, key="btn_p") if url_p.strip() else False

    with p2:
        st.markdown('<div class="yt-card">', unsafe_allow_html=True)
        st.markdown('<span class="yt-chip chip-red">Type</span>', unsafe_allow_html=True)
        pt_type = st.selectbox("Download As", ["🎬 Video / GIF (MP4)", "📸 HD Image (JPG)", "🎵 Audio from Pin (MP3)"], key="ptt")
        st.markdown('</div>', unsafe_allow_html=True)

    if dl_p_btn and url_p.strip():
        st.markdown("---")
        pb5 = st.progress(0); stxt5 = st.empty()
        pdir = os.path.join(WORK_DIR, "pin_run")
        shutil.rmtree(pdir, ignore_errors=True); os.makedirs(pdir, exist_ok=True)
        try:
            stxt5.markdown("📌 **Downloading Pinterest content...**"); pb5.progress(25)
            yopts_p = _ydl_base()
            yopts_p.update({'outtmpl': os.path.join(pdir, '%(id)s.%(ext)s'), 'ignoreerrors': True})
            if "Audio" in pt_type:
                yopts_p['format'] = 'bestaudio/best'
                yopts_p['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
            elif "Image" in pt_type:
                yopts_p['writethumbnail'] = True; yopts_p['skip_download'] = True
            else:
                yopts_p['format'] = 'bestvideo+bestaudio/best'; yopts_p['merge_output_format'] = 'mp4'

            with yt_dlp.YoutubeDL(yopts_p) as ydl: ydl.download([url_p.strip()])
            pb5.progress(90)
            
            pfiles = [os.path.join(pdir, f) for f in sorted(os.listdir(pdir)) if os.path.isfile(os.path.join(pdir, f))]
            if not pfiles:
                st.error("Download failed. Content may be private.")
            else:
                pb5.progress(100); stxt5.markdown(f"✅ **Downloaded {len(pfiles)} file(s)!**")
                for fp in pfiles:
                    fn = os.path.basename(fp); fs = os.path.getsize(fp)/(1024*1024); ext = fn.rsplit('.', 1)[-1].lower()
                    ico = "🎵" if ext == 'mp3' else ("🖼️" if ext in ('jpg', 'jpeg', 'png', 'webp', 'gif') else "🎬")
                    st.markdown(f'<div class="result-row"><span class="result-icon">{ico}</span><div><div class="result-name">{fn}</div><div class="result-sub">{ext.upper()} · {fs:.1f} MB</div></div></div>', unsafe_allow_html=True)
                    with open(fp, "rb") as fd:
                        pin_data = fd.read()
                    st.download_button(f"⬇ Download {fn[:45]}", pin_data, fn, use_container_width=True)
        except Exception as e:
            st.error(f"❌ {e}"); pb5.empty(); stxt5.empty()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 6: UNIVERSAL DOWNLOADER (FACEBOOK / TWITTER / TIKTOK / REDDIT)
# ═════════════════════════════════════════════════════════════════════════════
with tab_universal:
    st.markdown('<span class="yt-chip chip-blue">Universal Multi-Platform Downloader</span>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sec-title">Download videos, audio & media from Facebook, Twitter/X, TikTok, Reddit and 1,000+ sites</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="yt-card2" style="border-left: 3px solid #38bdf8; margin-bottom: 16px;">
        <div style="font-size: 0.85rem; line-height: 1.8;">
            <b>Supported Platforms:</b><br>
            📘 <b>Facebook</b> (Reels, Videos, Watch)<br>
            🐦 <b>Twitter / X</b> (Videos &amp; GIFs)<br>
            🎵 <b>TikTok</b> (Videos &amp; Sounds)<br>
            🤖 <b>Reddit</b> (Posts &amp; Videos with Audio)<br>
            🌐 Plus 1,000+ other web video platforms!
        </div>
    </div>
    """, unsafe_allow_html=True)

    u1, u2 = st.columns([3, 2], gap="large")
    with u1:
        url_u = st.text_input("Media URL", placeholder="Paste Facebook, Twitter/X, TikTok, or Reddit URL here...", key="url_u", label_visibility="collapsed")
        st.caption("Paste link from Facebook, X (Twitter), TikTok, Reddit, etc.")
        
        fcu, _ = st.columns([1, 3])
        with fcu:
            if st.button("🔍 Fetch Info", key="f_u"):
                if url_u.strip():
                    with st.spinner("Fetching platform info..."):
                        try: st.session_state['u_info'] = fetch_info(url_u.strip())
                        except Exception as e: st.error(str(e))

        if 'u_info' in st.session_state:
            video_info_card(st.session_state['u_info'])

        st.markdown("<br>", unsafe_allow_html=True)
        dl_u_btn = st.button("🌐 DOWNLOAD MEDIA NOW", type="primary", use_container_width=True, key="btn_u") if url_u.strip() else False

    with u2:
        st.markdown('<div class="yt-card">', unsafe_allow_html=True)
        st.markdown('<span class="yt-chip chip-blue">Format Options</span>', unsafe_allow_html=True)
        u_type = st.selectbox("Output Format", ["🎬 High Quality Video (MP4)", "🎵 Audio Only (MP3)", "🖼️ Thumbnail / Image"], key="utype")
        st.markdown('</div>', unsafe_allow_html=True)

    if dl_u_btn and url_u.strip():
        st.markdown("---")
        pb6 = st.progress(0); stxt6 = st.empty()
        udir = os.path.join(WORK_DIR, "uni_run")
        shutil.rmtree(udir, ignore_errors=True); os.makedirs(udir, exist_ok=True)
        try:
            stxt6.markdown("🌐 **Downloading media...**"); pb6.progress(25)
            yopts_u = _ydl_base()
            yopts_u.update({'outtmpl': os.path.join(udir, '%(title)s.%(ext)s'), 'ignoreerrors': True})
            if "MP3" in u_type:
                yopts_u['format'] = 'bestaudio/best'
                yopts_u['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
            elif "Image" in u_type:
                yopts_u['writethumbnail'] = True; yopts_u['skip_download'] = True
            else:
                yopts_u['format'] = 'bestvideo+bestaudio/best[ext=mp4]/best'
                yopts_u['merge_output_format'] = 'mp4'

            with yt_dlp.YoutubeDL(yopts_u) as ydl: ydl.download([url_u.strip()])
            pb6.progress(90)
            
            ufiles = [os.path.join(udir, f) for f in sorted(os.listdir(udir)) if os.path.isfile(os.path.join(udir, f))]
            if not ufiles:
                st.error("Could not download media. Please ensure the post/content is public.")
            else:
                pb6.progress(100); stxt6.markdown(f"✅ **Downloaded {len(ufiles)} file(s)!**")
                for fp in ufiles:
                    fn = os.path.basename(fp); fs = os.path.getsize(fp)/(1024*1024); ext = fn.rsplit('.', 1)[-1].lower()
                    ico = "🎵" if ext in ('mp3', 'm4a') else ("🖼️" if ext in ('jpg', 'png', 'webp') else "🎬")
                    st.markdown(f'<div class="result-row"><span class="result-icon">{ico}</span><div><div class="result-name">{fn[:65]}</div><div class="result-sub">{ext.upper()} · {fs:.1f} MB</div></div></div>', unsafe_allow_html=True)
                    with open(fp, "rb") as fd:
                        uni_data = fd.read()
                    st.download_button(f"⬇ Download {fn[:45]}", uni_data, fn, use_container_width=True)
        except Exception as e:
            st.error(f"❌ {e}"); pb6.empty(); stxt6.empty()
