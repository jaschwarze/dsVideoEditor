import os
import subprocess
import json


def _get_video_fps(video_path):
    try:
        command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "json",
            video_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

        output = json.loads(result.stdout)
        frame_rate = output["streams"][0]["r_frame_rate"]

        numerator, denominator = map(int, frame_rate.split("/"))
        fps = numerator / denominator
        return fps

    except Exception as e:
        print(f"Fehler beim Auslesen der FPS für Datei {video_path}: {e}")
        return None


def convert_video_file(input_file_path, output_file_path, aspect_ratio="4:3", audio_codec="aac", speed=1.0):
    if not os.path.exists(input_file_path) or not input_file_path.lower().endswith(".mp4") or os.path.isfile(output_file_path):
        return 0

    original_fps = _get_video_fps(input_file_path)
    if original_fps is None:
        return 0

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    if speed != 1.0:
        file_name = os.path.basename(input_file_path)
        file_name = "RAW-H264-" + file_name
        raw_file_path = os.path.join(os.path.dirname(input_file_path), file_name).replace(".mp4", ".h264")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", input_file_path,
                "-map", "0:v",
                "-c:v", "copy",
                "-bsf:v", "h264_mp4toannexb",
                raw_file_path
            ],
            check=True
        )

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-fflags", "+genpts",
                "-r", str(original_fps * speed),
                "-i", raw_file_path,
                "-i", input_file_path,
                "-map", "0:v",
                "-c:v", "copy",
                "-map", "1:a",
                "-af", f"atempo={speed}",
                "-aspect", aspect_ratio,
                "-acodec", audio_codec,
                "-movflags", "faststart",
                output_file_path
            ],
            check=True
        )

        os.unlink(raw_file_path)

    else:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", input_file_path,
                "-c:v", "copy",
                "-aspect", aspect_ratio,
                "-acodec", audio_codec,
                output_file_path
            ],
            check=True
        )
