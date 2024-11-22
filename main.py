import os
import shutil
import time
import argparse
from convert import convert_video_file


def _move_directory(source_dir, target_dir):
    if not os.path.exists(source_dir) or os.path.exists(target_dir):
        return

    os.makedirs(target_dir, exist_ok=True)
    moved_items = []
    try:
        for item in os.listdir(source_dir):
            source_path = os.path.join(source_dir, item)
            target_path = os.path.join(target_dir, item)

            if target_path.endswith(".MP4"):
                target_path = os.path.splitext(target_path)[0] + ".mp4"

            shutil.move(source_path, target_path)
            moved_items.append((target_path, source_path))
    except Exception as e:
        for moved_path, original_path in reversed(moved_items):
            shutil.move(moved_path, original_path)

    os.rmdir(source_dir)


def _get_dir_snapshot(dir_path):
    snapshot = {}
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, dir_path)
            snapshot[relative_path] = os.stat(file_path).st_mtime

    return snapshot


def _get_directory_contents(dir_path):
    contents = set()

    for root, dirs, files in os.walk(dir_path):
        relative_root = os.path.relpath(root, dir_path)

        if relative_root == ".":
            relative_root = ""

        for dir_name in dirs:
            contents.add(os.path.join(relative_root, dir_name))

        for file_name in files:
            contents.add(os.path.join(relative_root, file_name))

    return contents


def _is_folder_static(folder_path, wait_time=7):
    initial_snapshot = _get_dir_snapshot(folder_path)
    time.sleep(wait_time)
    current_snapshot = _get_dir_snapshot(folder_path)

    return initial_snapshot == current_snapshot


def _move_static_directories(input_path, output_path):
    if not os.path.isdir(input_path):
        return

    if not os.path.isdir(output_path):
        os.makedirs(output_path, exist_ok=True)

    for dir_name in os.listdir(input_path):
        dir_path = os.path.join(input_path, dir_name)

        if not os.path.isdir(dir_path):
            continue

        if _is_folder_static(dir_path):
            dir_output_path = os.path.join(output_path, dir_name)
            _move_directory(dir_path, dir_output_path)


def _convert_files_for_dir(input_path, output_path, aspect_ratio, audio_codec, speed):
    if not os.path.isdir(input_path):
        return

    if not os.path.isdir(output_path):
        os.makedirs(output_path, exist_ok=True)

    for order_name in os.listdir(input_path):
        order_path = os.path.join(input_path, order_name)

        if not os.path.isdir(order_path):
            continue

        output_order_path = order_path.replace(input_path, output_path)
        moved_non_video_files = []
        before_contents = _get_directory_contents(order_path)
        error = False

        try:
            for root, _, files in os.walk(order_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    output_file_path = file_path.replace(input_path, output_path)

                    if not file_path.endswith(".mp4"):
                        target_dir_path = os.path.dirname(output_file_path)

                        if not os.path.exists(target_dir_path):
                            os.makedirs(target_dir_path, exist_ok=True)

                        shutil.move(file_path, output_file_path)
                        moved_non_video_files.append((output_file_path, file_path))
                    else:
                        convert_video_file(file_path, output_file_path, aspect_ratio, audio_codec, speed)

        except Exception:
            error = True

            for moved_path, original_path in reversed(moved_non_video_files):
                shutil.move(moved_path, original_path)

            if len(output_order_path) > 0:
                shutil.rmtree(output_order_path)

        if not error:
            after_contents = _get_directory_contents(output_order_path)

            if before_contents == after_contents:
                if len(order_path) > 0:
                    shutil.rmtree(order_path)
            else:
                for root, _, files in os.walk(output_order_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        return_file_path = file_path.replace(output_path, input_path)

                        if not file_path.endswith(".mp4"):
                            shutil.move(file_path, return_file_path)

                if len(output_order_path) > 0:
                    shutil.rmtree(output_order_path)


def process_convert_directory(dir_path, aspect_ratio, audio_codec, speed=1.0):
    input_dir = os.path.join(dir_path, "Eingang")
    working_dir = os.path.join(dir_path, "Arbeitet")
    output_dir = os.path.join(dir_path, "Ausgang")

    _move_static_directories(input_dir, working_dir)
    _convert_files_for_dir(working_dir, output_dir, aspect_ratio, audio_codec, speed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_path", type=str, help="Input path")
    parser.add_argument("-ar", "--aspect_ratio", type=str, help="Video speed")
    parser.add_argument("-ac", "--audio_codec", type=str, help="Video speed")
    parser.add_argument("-s", "--video_speed", type=float, help="Video speed")
    args = parser.parse_args()

    process_convert_directory(args.input_path, args.aspect_ratio, args.audio_codec, args.video_speed)
