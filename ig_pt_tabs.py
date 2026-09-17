

# =============================================================================
#  TAB 5 — INSTAGRAM DOWNLOADER
# =============================================================================
with tab5:
    st.markdown('<span class="yt-chip" style="background:rgba(193,53,132,.15);color:#f472b6;border:1px solid rgba(193,53,132,.4);">Instagram Downloader</span>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sec-title">Download Instagram Reels, Videos, Photos, Carousels and extract MP3 audio</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="yt-card2" style="border-left:3px solid #f472b6;margin-bottom:16px;">
        <div style="font-size:.82rem;color:#aaa;line-height:2;">
            Supports: <b style="color:#f1f1f1;">Reels  |  Posts (Photo + Video)  |  Carousels  |  IGTV</b><br>
            Paste any public Instagram post, reel or video URL below.<br>
            Private accounts are NOT supported — only public content works.
        </div>
    </div>
    """, unsafe_allow_html=True)

    ci1, ci2 = st.columns([3, 2], gap="large")

    with ci1:
        url_ig = st.text_input("Instagram URL", placeholder="https://www.instagram.com/reel/...", key="url_ig", label_visibility="collapsed")
        st.caption("Paste Instagram reel / post / IGTV URL above")

        if st.button("Fetch Info", key="fetch_ig"):
            if url_ig.strip():
                with st.spinner("Fetching..."):
                    try:
                        ig_base = {"quiet": True, "no_warnings": True}
                        if FFMPEG_DIR:
                            ig_base["ffmpeg_location"] = FFMPEG_DIR
                        with yt_dlp.YoutubeDL(ig_base) as ydl:
                            st.session_state["ig_info"] = ydl.extract_info(url_ig.strip(), download=False)
                    except Exception as e:
                        st.error(str(e))

        if "ig_info" in st.session_state:
            ig      = st.session_state["ig_info"]
            ig_t    = (ig.get("title") or ig.get("description") or "Instagram Post")[:80]
            ig_up   = ig.get("uploader") or "Unknown"
            ig_thb  = ig.get("thumbnail", "")
            ig_dur  = int(ig.get("duration", 0))
            ig_ents = ig.get("entries", [])
            is_car  = len(ig_ents) > 1

            thb_html = f'<img class="vid-thumb" src="{ig_thb}" />' if ig_thb else '<div style="width:80px;height:80px;background:#2a2a2a;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:2rem;">📸</div>'
            dur_html = f'<div class="vid-meta">Duration: {ig_dur//60}m {ig_dur%60}s</div>' if ig_dur else ""
            car_html = f'<div class="vid-meta" style="color:#f472b6;">Carousel: {len(ig_ents)} items</div>' if is_car else ""

            st.markdown(f"""
            <div class="yt-card2" style="border-left:3px solid #f472b6;">
                <div class="vid-row">
                    {thb_html}
                    <div>
                        <div class="vid-title">{ig_t}</div>
                        <div class="vid-meta">@{ig_up}</div>
                        {dur_html}{car_html}
                        <span class="vid-badge" style="background:#c13584;">READY</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        dl_ig_btn5 = st.button("DOWNLOAD FROM INSTAGRAM", type="primary", use_container_width=True, key="dl_ig") if url_ig.strip() else False

    with ci2:
        st.markdown('<div class="yt-card">', unsafe_allow_html=True)
        st.markdown('<span class="yt-chip" style="background:rgba(193,53,132,.15);color:#f472b6;border:1px solid rgba(193,53,132,.3);">Options</span>', unsafe_allow_html=True)

        ig_type5 = st.selectbox("What to Download", [
            "Video or Reel (MP4)",
            "Audio Only (MP3)",
            "Photo (JPG)",
            "All Items ZIP (Carousel)",
        ], key="ig_type5")

        if "MP3" in ig_type5:
            ig_aq5  = st.selectbox("Audio Quality", ["320 kbps", "256 kbps", "192 kbps", "128 kbps"], key="ig_aq5")
            ig_br5  = ig_aq5.split()[0]
            ig_vf5  = None
        else:
            ig_vl5 = st.selectbox("Video Quality", ["Best Available", "1080p", "720p", "480p"], key="ig_vq5")
            ig_vf5 = {
                "Best Available": "bestvideo+bestaudio/best",
                "1080p": "bestvideo[height<=1080]+bestaudio/best",
                "720p":  "bestvideo[height<=720]+bestaudio/best",
                "480p":  "bestvideo[height<=480]+bestaudio/best"
            }.get(ig_vl5, "bestvideo+bestaudio/best")
            ig_br5 = None

        st.markdown("""
        <div class="yt-card3" style="margin-top:12px;">
            <div style="font-size:.78rem;color:#aaa;line-height:1.9;">
                Video/Reel — Download as MP4<br>
                MP3 — Extract audio from reel<br>
                Photo — Save post image as JPG<br>
                Carousel ZIP — All items in one file
            </div>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if dl_ig_btn5 and url_ig.strip():
        st.markdown("---")
        pb5  = st.progress(0)
        stx5 = st.empty()
        ig_dir = os.path.join(WORK_DIR, "ig_out")
        shutil.rmtree(ig_dir, ignore_errors=True)
        os.makedirs(ig_dir, exist_ok=True)
        try:
            stx5.markdown("Downloading from Instagram..."); pb5.progress(20)
            ig_ydl5 = {
                "outtmpl": os.path.join(ig_dir, "%(id)s.%(ext)s"),
                "quiet": True, "no_warnings": True
            }
            if FFMPEG_DIR:
                ig_ydl5["ffmpeg_location"] = FFMPEG_DIR
            if "MP3" in ig_type5:
                ig_ydl5["format"] = "bestaudio/best"
                ig_ydl5["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": ig_br5}]
            elif "Photo" in ig_type5:
                ig_ydl5["writethumbnail"] = True
                ig_ydl5["skip_download"] = True
            else:
                ig_ydl5["format"] = ig_vf5 or "bestvideo+bestaudio/best"
                ig_ydl5["merge_output_format"] = "mp4"
            with yt_dlp.YoutubeDL(ig_ydl5) as ydl:
                ydl.download([url_ig.strip()])
            pb5.progress(95)
            files5 = [os.path.join(ig_dir, f) for f in sorted(os.listdir(ig_dir)) if os.path.isfile(os.path.join(ig_dir, f))]
            if not files5:
                st.error("No files found. Content may be private or unsupported.")
            else:
                pb5.progress(100)
                stx5.markdown(f"Done! {len(files5)} file(s) downloaded.")
                if len(files5) > 2:
                    zp5 = os.path.join(ig_dir, "instagram.zip")
                    with zipfile.ZipFile(zp5, "w") as zf:
                        for fp in files5:
                            zf.write(fp, os.path.basename(fp))
                    with open(zp5, "rb") as zd:
                        st.download_button("Download All (ZIP)", zd, "instagram.zip", "application/zip", use_container_width=True)
                else:
                    for fp in files5:
                        fn  = os.path.basename(fp)
                        fs  = os.path.getsize(fp) / (1024 * 1024)
                        ext = fn.rsplit(".", 1)[-1].lower()
                        ico = "Audio" if ext in ("mp3", "m4a") else ("Image" if ext in ("jpg", "jpeg", "png", "webp") else "Video")
                        mim = "audio/mpeg" if ext == "mp3" else ("image/jpeg" if ext in ("jpg", "png", "webp") else "video/mp4")
                        st.write(f"{ico}: {fn} ({fs:.1f} MB)")
                        with open(fp, "rb") as fd:
                            st.download_button(f"Download — {fn[:45]}", fd, fn, mim, key=f"ig5_{fn}", use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
            pb5.empty(); stx5.empty()


# =============================================================================
#  TAB 6 — PINTEREST DOWNLOADER
# =============================================================================
with tab6:
    st.markdown('<span class="yt-chip" style="background:rgba(230,0,35,.15);color:#f87171;border:1px solid rgba(230,0,35,.35);">Pinterest Downloader</span>', unsafe_allow_html=True)
    st.markdown('<div class="yt-sec-title">Download Pinterest Videos, GIFs, HD Images and Board collections as ZIP</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="yt-card2" style="border-left:3px solid #f87171;margin-bottom:16px;">
        <div style="font-size:.82rem;color:#aaa;line-height:2;">
            Supports: <b style="color:#f1f1f1;">Pin Videos  |  GIFs  |  HD Images  |  Board (multiple pins)</b><br>
            Paste any public Pinterest pin URL or board URL below.<br>
            Secret boards are NOT supported.
        </div>
    </div>
    """, unsafe_allow_html=True)

    cp1, cp2 = st.columns([3, 2], gap="large")

    with cp1:
        url_pt = st.text_input("Pinterest URL", placeholder="https://www.pinterest.com/pin/... or /username/board-name/", key="url_pt", label_visibility="collapsed")
        st.caption("Paste Pinterest pin or board URL above")

        if st.button("Fetch Info", key="fetch_pt"):
            if url_pt.strip():
                with st.spinner("Fetching..."):
                    try:
                        pt_base = {"quiet": True, "no_warnings": True}
                        if FFMPEG_DIR:
                            pt_base["ffmpeg_location"] = FFMPEG_DIR
                        with yt_dlp.YoutubeDL(pt_base) as ydl:
                            st.session_state["pt_info"] = ydl.extract_info(url_pt.strip(), download=False)
                    except Exception as e:
                        st.error(str(e))

        if "pt_info" in st.session_state:
            pt      = st.session_state["pt_info"]
            pt_t    = (pt.get("title") or pt.get("description") or "Pinterest Pin")[:80]
            pt_up   = pt.get("uploader") or "Unknown"
            pt_thb  = pt.get("thumbnail", "")
            pt_dur  = int(pt.get("duration", 0))
            pt_ents = pt.get("entries", [])

            thb2 = f'<img class="vid-thumb" src="{pt_thb}" />' if pt_thb else '<div style="width:80px;height:80px;background:#2a2a2a;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:2rem;">📌</div>'
            dur2 = f'<div class="vid-meta">Duration: {pt_dur//60}m {pt_dur%60}s</div>' if pt_dur else ""
            brd2 = f'<div class="vid-meta" style="color:#f87171;">Board: {len(pt_ents)} pins found</div>' if pt_ents else ""

            st.markdown(f"""
            <div class="yt-card2" style="border-left:3px solid #f87171;">
                <div class="vid-row">
                    {thb2}
                    <div>
                        <div class="vid-title">{pt_t}</div>
                        <div class="vid-meta">{pt_up}</div>
                        {dur2}{brd2}
                        <span class="vid-badge" style="background:#e60023;">READY</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        dl_pt_btn6 = st.button("DOWNLOAD FROM PINTEREST", type="primary", use_container_width=True, key="dl_pt") if url_pt.strip() else False

    with cp2:
        st.markdown('<div class="yt-card">', unsafe_allow_html=True)
        st.markdown('<span class="yt-chip" style="background:rgba(230,0,35,.15);color:#f87171;border:1px solid rgba(230,0,35,.3);">Options</span>', unsafe_allow_html=True)

        pt_type6 = st.selectbox("What to Download", [
            "Video or GIF (MP4)",
            "Image (Best Quality JPG)",
            "Audio from Video (MP3)",
        ], key="pt_type6")

        if "MP3" in pt_type6:
            pt_aq6  = st.selectbox("Audio Quality", ["320 kbps", "192 kbps", "128 kbps"], key="pt_aq6")
            pt_br6  = pt_aq6.split()[0]
            pt_vf6  = None
        else:
            pt_vl6 = st.selectbox("Quality", ["Best Available", "1080p", "720p", "480p"], key="pt_vq6")
            pt_vf6 = {
                "Best Available": "bestvideo+bestaudio/best",
                "1080p": "bestvideo[height<=1080]+bestaudio/best",
                "720p":  "bestvideo[height<=720]+bestaudio/best",
                "480p":  "bestvideo[height<=480]+bestaudio/best"
            }.get(pt_vl6, "bestvideo+bestaudio/best")
            pt_br6 = None

        pt_has_board = bool(st.session_state.get("pt_info", {}).get("entries"))
        pt_lim6 = st.slider("Board: Max Pins", 1, 50, 10, key="ptlim6") if pt_has_board else None

        st.markdown("""
        <div class="yt-card3" style="margin-top:12px;">
            <div style="font-size:.78rem;color:#aaa;line-height:1.9;">
                Single Pin — Video, GIF, or Image<br>
                Board — Multiple pins in ZIP<br>
                MP3 — Extract audio from pin video<br>
                Board downloads are auto-zipped
            </div>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if dl_pt_btn6 and url_pt.strip():
        st.markdown("---")
        pb6  = st.progress(0)
        stx6 = st.empty()
        pt_dir = os.path.join(WORK_DIR, "pt_out")
        shutil.rmtree(pt_dir, ignore_errors=True)
        os.makedirs(pt_dir, exist_ok=True)
        try:
            stx6.markdown("Connecting to Pinterest..."); pb6.progress(15)
            pt_ydl6 = {
                "outtmpl": os.path.join(pt_dir, "%(id)s.%(ext)s"),
                "quiet": True, "no_warnings": True
            }
            if FFMPEG_DIR:
                pt_ydl6["ffmpeg_location"] = FFMPEG_DIR
            if pt_lim6:
                pt_ydl6["playlist_end"] = pt_lim6
            if "MP3" in pt_type6:
                pt_ydl6["format"] = "bestaudio/best"
                pt_ydl6["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": pt_br6}]
            elif "Image" in pt_type6:
                pt_ydl6["writethumbnail"] = True
                pt_ydl6["skip_download"] = True
            else:
                pt_ydl6["format"] = pt_vf6 or "bestvideo+bestaudio/best"
                pt_ydl6["merge_output_format"] = "mp4"

            pb6.progress(30); stx6.markdown("Downloading Pinterest content...")
            with yt_dlp.YoutubeDL(pt_ydl6) as ydl:
                ydl.download([url_pt.strip()])
            pb6.progress(90)

            files6 = [os.path.join(pt_dir, f) for f in sorted(os.listdir(pt_dir)) if os.path.isfile(os.path.join(pt_dir, f))]
            if not files6:
                st.error("No files downloaded. May be private or unsupported.")
            else:
                pb6.progress(100)
                stx6.markdown(f"Done! {len(files6)} file(s) downloaded from Pinterest!")
                if len(files6) > 2:
                    zp6 = os.path.join(pt_dir, "pinterest_board.zip")
                    with zipfile.ZipFile(zp6, "w") as zf:
                        for fp in files6:
                            zf.write(fp, os.path.basename(fp))
                    with open(zp6, "rb") as zd:
                        st.download_button("Download Board ZIP", zd, "pinterest_board.zip", "application/zip", use_container_width=True)
                    st.caption(f"{len(files6)} files included in ZIP")
                else:
                    for fp in files6:
                        fn  = os.path.basename(fp)
                        fs  = os.path.getsize(fp) / (1024 * 1024)
                        ext = fn.rsplit(".", 1)[-1].lower()
                        ico = "Audio" if ext == "mp3" else ("Image" if ext in ("jpg", "jpeg", "png", "webp", "gif") else "Video")
                        mim = "audio/mpeg" if ext == "mp3" else ("image/jpeg" if ext in ("jpg", "png", "webp") else "video/mp4")
                        st.write(f"{ico}: {fn} ({fs:.1f} MB)")
                        with open(fp, "rb") as fd:
                            st.download_button(f"Download — {fn[:45]}", fd, fn, mim, key=f"pt6_{fn}", use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
            pb6.empty(); stx6.empty()
