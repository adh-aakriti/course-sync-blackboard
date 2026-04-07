import os
from extractor import extract_text


def clean_text(text):
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()
        if line:
            cleaned.append(line)

    return "\n".join(cleaned).strip()


def is_supported_file(filename):
    lower = filename.lower()
    return lower.endswith(".pdf") or lower.endswith(".pptx") or lower.endswith(".ppt")


def build_masterfile(course_path, course_name):
    master_text = f"""COURSE: {course_name}

This file contains all extracted lecture material for this course.
Each section corresponds to one downloaded file.

====================================
"""

    files = sorted(os.listdir(course_path))

    for file in files:
        full_path = os.path.join(course_path, file)

        if os.path.isdir(full_path):
            continue

        if file == "MASTERFILE.txt" or file == "download_manifest.json":
            continue

        if not is_supported_file(file):
            continue

        print(f"Extracting: {file}")

        text = extract_text(full_path)
        text = clean_text(text)

        session_name = file.rsplit(".", 1)[0]

        if not text:
            text = "[No extractable text found]"

        master_text += f"""

FILE: {file}
SECTION: {session_name}

CONTENT:
{text}

------------------------------------
"""

    output_path = os.path.join(course_path, "MASTERFILE.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(master_text.strip())

    return output_path