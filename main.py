import os
import ffmpeg
import shutil

INPUT_PATH = "./input"
OUTPUT_PATH = "./output"
ERROR_PATH = "./error"


def _get_video_fps(video_path):
    probe = ffmpeg.probe(video_path)
    video_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
    if video_streams:
        return float(video_streams[0]["r_frame_rate"].split("/")[0]) / float(video_streams[0]["r_frame_rate"].split("/")[1])

    return None

def _move_directory(source_dir, target_dir):
    if not os.path.exists(source_dir):
        return

    if os.path.exists(target_dir):
        return

    os.makedirs(target_dir)

    moved_items = []
    try:
        for item in os.listdir(source_dir):
            source_path = os.path.join(source_dir, item)
            target_path = os.path.join(target_dir, item)

            shutil.move(source_path, target_path)
            moved_items.append((target_path, source_path))
    except Exception as e:
        for moved_path, original_path in reversed(moved_items):
            shutil.move(moved_path, original_path)

    os.rmdir(source_dir)

def convert_video_file(input_file_path, output_file_path, aspect_ratio="4:3", audio_codec="aac", speed=1.0):
    if not os.path.exists(input_file_path) or not input_file_path.lower().endswith(".mp4") or os.path.isfile(output_file_path):
        return 0

    original_fps = _get_video_fps(input_file_path)
    if original_fps is None:
        return 0

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    if speed != 1.0:
        video_speed_filter = f"{1 / speed}*PTS" if speed != 1.0 else None
        audio_speed_filter = f"{speed}" if speed != 1.0 else None

        file_name = os.path.basename(input_file_path)
        file_name = "RAW-H264-" + file_name
        raw_file_path = os.path.join(os.path.dirname(input_file_path), file_name).replace(".mp4", ".h264")

        (
            ffmpeg
            .input(input_file_path)
            .output(raw_file_path, map="0:v", c="copy", bsf="h264_mp4toannexb")
            .run(overwrite_output=True)
        )

        (
            ffmpeg
            .input(raw_file_path, fflags="+genpts", r=original_fps * speed)
            .output(
                output_file_path,
                c="copy",
                aspect=aspect_ratio
            )
            .run(overwrite_output=True)
        )

    else:
        stream = ffmpeg.input(input_file_path)
        stream = ffmpeg.output(
            stream,
            output_file_path,
            aspect=aspect_ratio,
            acodec=audio_codec
        )

        ffmpeg.run(stream)

if __name__ == "__main__":
    i_path = "./input/order-11111111/Quelle/1578318-hd_1920_1080_30fps.mp4"
    o_path = "./output/order-11111111/Quelle/1578318-hd_1920_1080_30fps.mp4"
    convert_video_file(i_path, o_path, speed=0.5)


    # TODO: speed 1.31 und 0.72