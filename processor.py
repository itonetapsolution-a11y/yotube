import os
import shutil
import subprocess
import static_ffmpeg

def init_ffmpeg():
    """
    Ensure ffmpeg is in system PATH.
    """
    if not shutil.which('ffmpeg'):
        try:
            static_ffmpeg.add_paths()
        except Exception:
            pass

def get_video_duration(input_path):
    """
    Get duration of video in seconds using ffprobe.
    """
    init_ffmpeg()
    ffprobe_path = shutil.which('ffprobe') or 'ffprobe'
    cmd = [
        ffprobe_path,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise ValueError(f"ffprobe failed: {e.stderr}")
    except Exception as e:
        raise ValueError(f"Error running ffprobe: {e}")

def _run_ffmpeg_shorts(
    input_path, 
    output_path, 
    start_time, 
    clip_duration, 
    aspect_ratio="9:16", 
    mode='blur', 
    watermark_text=None,
    text_position="top",
    text_style="yellow_box",
    subtitle_path=None
):
    """
    FFmpeg video converter with aspect ratio selection, stylish text overlay, and subtitles.
    """
    # Resolution map
    res_map = {
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "1:1": (1080, 1080),
        "4:5": (1080, 1350)
    }
    target_w, target_h = res_map.get(aspect_ratio, (1080, 1920))

    ffmpeg_path = shutil.which('ffmpeg') or 'ffmpeg'
    cmd = [ffmpeg_path, '-y', '-ss', str(start_time), '-t', str(clip_duration), '-i', input_path]
    filter_complex = []
    
    # 1. Base Aspect Ratio Filter
    if mode == 'blur':
        vf = (
            f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},boxblur=25:10[bg];"
            f"[0:v]scale={target_w}:-1:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[vbase]"
        )
        filter_complex.append(vf)
        last_node = "[vbase]"
    elif mode == 'crop':
        vf = f"[0:v]scale=-1:{target_h},crop={target_w}:{target_h}[vbase]"
        filter_complex.append(vf)
        last_node = "[vbase]"
    else: # fit
        vf = f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:({target_w}-iw)/2:({target_h}-ih)/2:black[vbase]"
        filter_complex.append(vf)
        last_node = "[vbase]"

    # 2. Text / Song Title Overlay Filter
    if watermark_text and watermark_text.strip():
        clean_text = watermark_text.strip().replace("'", "").replace(":", "\\:").replace("%", "\\%")
        
        # Position calculation
        if text_position == "top":
            y_pos = "70"
        elif text_position == "bottom":
            y_pos = f"{target_h - 130}"
        else: # center
            y_pos = "(h-text_h)/2"

        # Style configuration
        if text_style == "yellow_box":
            style_params = "fontcolor=yellow:fontsize=36:box=1:boxcolor=black@0.75:boxborderw=12"
        elif text_style == "neon_cyan":
            style_params = "fontcolor=0x00FFFF:fontsize=36:box=1:boxcolor=0x000000@0.85:boxborderw=12"
        elif text_style == "red_badge":
            style_params = "fontcolor=white:fontsize=36:box=1:boxcolor=0xFF0000@0.8:boxborderw=12"
        else: # white_shadow
            style_params = "fontcolor=white:fontsize=38:shadowcolor=black:shadowx=4:shadowy=4"

        txt_vf = f"{last_node}drawtext=text='{clean_text}':x=(w-text_w)/2:y={y_pos}:{style_params}[vtxt]"
        filter_complex.append(txt_vf)
        last_node = "[vtxt]"

    # 3. Subtitles Overlay Filter
    clean_sub_file = None
    if subtitle_path and os.path.exists(subtitle_path):
        out_dir = os.path.dirname(output_path)
        clean_sub_file = os.path.join(out_dir, "temp_subs.srt")
        try:
            shutil.copyfile(subtitle_path, clean_sub_file)
        except Exception:
            clean_sub_file = subtitle_path

    if clean_sub_file and os.path.exists(clean_sub_file):
        sub_escaped = clean_sub_file.replace('\\', '/').replace(':', '\\:')
        sub_vf = f"{last_node}subtitles='{sub_escaped}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2'[vsub]"
        filter_complex.append(sub_vf)
        last_node = "[vsub]"

    full_filter = ";".join(filter_complex)
    
    cmd.extend([
        '-filter_complex', full_filter,
        '-map', last_node,
        '-map', '0:a?',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '22',
        '-c:a', 'aac',
        '-b:a', '128k',
        output_path
    ])
    
    print("Running FFmpeg:", " ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Cleanup temp subs
    if clean_sub_file and clean_sub_file != subtitle_path and os.path.exists(clean_sub_file):
        try:
            os.remove(clean_sub_file)
        except Exception:
            pass

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg returned code {result.returncode}: {result.stderr}")
        
    return output_path

def process_shorts_clip(
    input_path, 
    output_path, 
    start_time, 
    clip_duration, 
    aspect_ratio="9:16", 
    mode='blur', 
    watermark_text=None,
    text_position="top",
    text_style="yellow_box",
    subtitle_path=None
):
    """
    Process clip with automatic fallback if subtitles fail.
    """
    init_ffmpeg()
    
    # Try with subtitles first if provided
    if subtitle_path and os.path.exists(subtitle_path):
        try:
            return _run_ffmpeg_shorts(
                input_path, output_path, start_time, clip_duration, 
                aspect_ratio=aspect_ratio, mode=mode, 
                watermark_text=watermark_text, text_position=text_position, text_style=text_style,
                subtitle_path=subtitle_path
            )
        except Exception as sub_err:
            print(f"Subtitle burn failed ({sub_err}). Retrying without subtitles...")
            
    # Fallback without subtitles
    return _run_ffmpeg_shorts(
        input_path, output_path, start_time, clip_duration, 
        aspect_ratio=aspect_ratio, mode=mode, 
        watermark_text=watermark_text, text_position=text_position, text_style=text_style,
        subtitle_path=None
    )

def generate_all_shorts(
    video_path, 
    output_dir, 
    clip_length=30, 
    max_clips=5, 
    aspect_ratio="9:16",
    mode='blur', 
    watermark_text=None,
    text_position="top",
    text_style="yellow_box",
    subtitle_path=None, 
    progress_callback=None
):
    """
    Generate multiple clips with aspect ratio, text overlay, and subtitles.
    """
    os.makedirs(output_dir, exist_ok=True)
    duration = get_video_duration(video_path)
    if duration <= 0:
        raise ValueError("Invalid video duration.")

    generated_clips = []
    start = 0.0
    clip_num = 1

    while start + 5.0 < duration and clip_num <= max_clips:
        actual_clip_duration = min(clip_length, duration - start)
        clip_filename = f"Clip_{clip_num:02d}_{aspect_ratio.replace(':', 'x')}_{int(start)}s_to_{int(start + actual_clip_duration)}s.mp4"
        out_path = os.path.join(output_dir, clip_filename)
        
        if progress_callback:
            progress_callback(clip_num, max_clips, f"Generating Clip #{clip_num} ({aspect_ratio}) ({int(start)}s - {int(start + actual_clip_duration)}s)...")

        process_shorts_clip(
            video_path, out_path, start, actual_clip_duration, 
            aspect_ratio=aspect_ratio, mode=mode, 
            watermark_text=watermark_text, text_position=text_position, text_style=text_style,
            subtitle_path=subtitle_path
        )
        generated_clips.append(out_path)

        start += actual_clip_duration
        clip_num += 1

    return generated_clips
