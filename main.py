import os
from masterfile_builder import build_masterfile

COURSES_BASE = "Courses"


def main():
    if not os.path.exists(COURSES_BASE):
        print("Courses folder not found.")
        return

    for course_name in os.listdir(COURSES_BASE):
        course_path = os.path.join(COURSES_BASE, course_name)

        if not os.path.isdir(course_path):
            continue

        print(f"\nBuilding MASTERFILE for: {course_name}")
        output_path = build_masterfile(course_path, course_name)
        print(f"Created: {output_path}")


if __name__ == "__main__":
    main()