# CourseSync

## Overview

Students often need to manually download multiple PDFs and lecture slides from Blackboard, organize them, and then re-upload them into study tools or Large Language Models (LLMs).

This process is repetitive, time-consuming, and unstructured.

CourseSync automates this workflow by extracting course materials, organizing them locally, and generating a single structured file (`MASTERFILE.txt`) per course.

---

## Features

- Automated Blackboard content extraction using Selenium
- Dynamic expansion of course modules and folders
- Download of lecture materials (PDF, PPT, PPTX)
- File organization by course
- Duplicate handling using file hashing and tracking
- Text extraction from PDF and PowerPoint files
- Graceful handling of invalid or unsupported files
- Generation of a single structured `MASTERFILE.txt` per course

---

## Workflow

1. Run `scraper.py`
2. Log into Blackboard and open a course Content page
3. Files are downloaded automatically
4. Run `main.py`
5. `MASTERFILE.txt` is generated for each course

---

## Project Structure


course-sync/

scraper.py

extractor.py

masterfile_builder.py

main.py

Courses/

SAMPLE_COURSE/

MASTERFILE.txt

download_manifest.json

---

## Example Output

Each course produces a folder containing downloaded materials and a unified file:


Courses/
COURSE_NAME/
MASTERFILE.txt


The MASTERFILE contains structured lecture content such as SQL concepts, database structures, and analytical techniques for database course.

---

## Problem Solved

This system removes the need to:
- manually download multiple files
- organize them into folders
- upload them again for study or summarization

Instead, it provides a single unified study resource per course.

---

## Limitations

- Requires manual login to Blackboard
- Blackboard content structure varies across courses
- Some Blackboard “documents” are not real files and are skipped
- File naming is simplified for robustness
- Extraction depends on file format quality

---

## Future Improvement

- Smarter content structuring inside MASTERFILE:
  - Detect sessions and modules more accurately
  - Improve hierarchy (Course → Session → Topic)
  - Reduce redundancy between overlapping lecture materials

---

## Requirements

- Python 3.x
- selenium
- webdriver-manager
- pdfplumber
- python-pptx

Install dependencies:


pip install selenium webdriver-manager pdfplumber python-pptx


---

## How to Run


python scraper.py


Then:


python main.py
