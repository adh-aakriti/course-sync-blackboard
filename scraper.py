import os
import json
import time
import hashlib
import shutil

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager


BLACKBOARD_URL = "https://blackboard.ie.edu/ultra"
COURSES_BASE_FOLDER = "Courses"
DOWNLOADS_FOLDER = os.path.join(os.getcwd(), "browser_downloads")
SCROLL_PAUSE = 1.2


def create_driver():
    os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    prefs = {
        "download.default_directory": DOWNLOADS_FOLDER,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


def safe_filename(name):
    bad_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for ch in bad_chars:
        name = name.replace(ch, "_")
    return name.strip()


def scroll_to_bottom(driver, pause=SCROLL_PAUSE, max_rounds=20):
    last_height = driver.execute_script("return document.body.scrollHeight")

    for _ in range(max_rounds):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def clear_browser_downloads_folder():
    os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)
    for name in os.listdir(DOWNLOADS_FOLDER):
        path = os.path.join(DOWNLOADS_FOLDER, name)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except Exception:
                pass


def list_downloaded_files():
    return {
        name for name in os.listdir(DOWNLOADS_FOLDER)
        if os.path.isfile(os.path.join(DOWNLOADS_FOLDER, name))
    }


def wait_for_new_download(before_files, timeout=60):
    start = time.time()

    while time.time() - start < timeout:
        current_files = list_downloaded_files()

        # ignore incomplete downloads
        incomplete = [f for f in current_files if f.endswith(".crdownload")]
        if incomplete:
            time.sleep(1)
            continue

        new_files = current_files - before_files
        if new_files:
            # return newest file by mtime
            candidates = [os.path.join(DOWNLOADS_FOLDER, f) for f in new_files]
            candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return candidates[0]

        time.sleep(1)

    return None


def is_allowed_filename(name):
    name = name.lower()
    return name.endswith(".pdf") or name.endswith(".ppt") or name.endswith(".pptx")


def get_unique_filepath(folder, filename):
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(folder, filename)
    counter = 2

    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{base} ({counter}){ext}")
        counter += 1

    return candidate


def manifest_path(course_folder):
    return os.path.join(course_folder, "download_manifest.json")


def load_manifest(course_folder):
    path = manifest_path(course_folder)
    if not os.path.exists(path):
        return {"downloads": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"downloads": []}


def save_manifest(course_folder, manifest):
    path = manifest_path(course_folder)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def source_id_exists(manifest, source_id):
    for item in manifest.get("downloads", []):
        if item.get("source_id") == source_id:
            return True
    return False


def hash_exists(manifest, sha256_hash):
    for item in manifest.get("downloads", []):
        if item.get("sha256") == sha256_hash:
            return True
    return False


def add_manifest_entry(manifest, source_id, saved_name, sha256_hash):
    manifest.setdefault("downloads", []).append({
        "source_id": source_id,
        "saved_name": saved_name,
        "sha256": sha256_hash
    })


def detect_course_name(driver):
    possible_selectors = ["header", "h1", "h2", "div"]
    ignored = {
        "courses", "content", "calendar", "announcements", "discussions",
        "gradebook", "messages", "groups", "achievements", "open"
    }

    for selector in possible_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.text.strip()
                if not text:
                    continue

                lines = [line.strip() for line in text.split("\n") if line.strip()]
                for line in lines:
                    lowered = line.lower()
                    if lowered in ignored:
                        continue
                    if len(line) > 3 and line.isupper():
                        return safe_filename(line)
        except Exception:
            continue

    title = driver.title.strip()
    if title:
        return safe_filename(title)

    return "Unknown Course"


def expand_all_sections(driver):
    print("Expanding ALL folders/modules...")

    for _ in range(10):
        buttons = driver.find_elements(By.XPATH, "//button[@aria-expanded='false']")

        if not buttons:
            break

        for btn in buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.2)
            except Exception:
                continue


def collect_visible_file_items(driver):
    items = driver.execute_script("""
        const nodes = Array.from(document.querySelectorAll("[data-content-id]"));
        const results = [];

        function clean(s) {
            return (s || "").trim();
        }

        function isAllowedFile(name) {
            const lower = name.toLowerCase();
            return lower.endsWith(".pdf") || lower.endsWith(".ppt") || lower.endsWith(".pptx");
        }

        for (const node of nodes) {
            const text = clean(node.innerText);
            if (!text) continue;

            const lines = text.split("\\n").map(s => s.trim()).filter(Boolean);
            if (!lines.length) continue;

            let filename = null;
            for (const line of lines) {
                if (isAllowedFile(line)) {
                    filename = line;
                    break;
                }
            }

            if (!filename) continue;

            const contentId = node.getAttribute("data-content-id") || "";
            results.push({
                filename,
                contentId
            });
        }

        return results;
    """)

    files = []
    seen = set()

    for item in items:
        filename = item["filename"].strip()
        content_id = item["contentId"].strip()

        if not is_allowed_filename(filename):
            continue

        key = (filename, content_id)
        if key in seen:
            continue
        seen.add(key)

        files.append({
            "name": safe_filename(filename),
            "content_id": content_id
        })

    return files


def find_file_row_by_content_id(driver, content_id):
    return driver.find_element(By.CSS_SELECTOR, f'[data-content-id="{content_id}"]')


def click_more_options_on_row(driver, row):
    possible_selectors = [
        './/button[contains(@aria-label, "More options")]',
        './/button[contains(@aria-label, "more options")]',
        './/button[contains(@aria-label, "More Actions")]',
        './/button[contains(@aria-label, "more")]',
        './/button[@aria-haspopup="menu"]',
        './/button'
    ]

    for selector in possible_selectors:
        try:
            candidates = row.find_elements(By.XPATH, selector)
            for btn in candidates:
                try:
                    ActionChains(driver).move_to_element(btn).perform()
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    return True
                except Exception:
                    continue
        except Exception:
            continue

    return False


def click_download_original_file(driver):
    menu_selectors = [
        '//span[contains(normalize-space(), "Download Original File")]',
        '//button[contains(normalize-space(), "Download Original File")]',
        '//a[contains(normalize-space(), "Download Original File")]',
        '//*[contains(normalize-space(), "Download Original File")]'
    ]

    for selector in menu_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for el in elements:
                try:
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(1)
                    return True
                except Exception:
                    continue
        except Exception:
            continue

    return False


def move_download_to_course_folder(downloaded_path, course_folder, desired_name, manifest, source_id):
    actual_downloaded_name = os.path.basename(downloaded_path)

    if not is_allowed_filename(actual_downloaded_name) and not is_allowed_filename(desired_name):
        try:
            os.remove(downloaded_path)
        except Exception:
            pass
        print(f"Skipped unsupported: {actual_downloaded_name}")
        return

    ext = os.path.splitext(actual_downloaded_name)[1]
    if not ext:
        ext = os.path.splitext(desired_name)[1]

    if not ext:
        try:
            os.remove(downloaded_path)
        except Exception:
            pass
        print(f"Skipped unknown file type: {actual_downloaded_name}")
        return

    base_name = os.path.splitext(desired_name)[0]
    final_name = safe_filename(base_name + ext)

    sha256_hash = file_sha256(downloaded_path)

    if hash_exists(manifest, sha256_hash):
        try:
            os.remove(downloaded_path)
        except Exception:
            pass
        print(f"Skipped already-downloaded content: {final_name}")
        return

    final_path = get_unique_filepath(course_folder, final_name)
    shutil.move(downloaded_path, final_path)

    add_manifest_entry(manifest, source_id, os.path.basename(final_path), sha256_hash)
    print(f"Downloaded: {os.path.basename(final_path)}")


def download_one_file_via_browser(driver, course_folder, file_item, manifest):
    source_id = file_item["content_id"] or file_item["name"]

    if source_id_exists(manifest, source_id):
        print(f"Skipped already-downloaded source: {file_item['name']}")
        return

    try:
        row = find_file_row_by_content_id(driver, file_item["content_id"])
    except Exception:
        print(f"Could not refind row for: {file_item['name']}")
        return

    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
        time.sleep(0.5)
    except Exception:
        pass

    before_files = list_downloaded_files()

    if not click_more_options_on_row(driver, row):
        print(f"Could not open menu for: {file_item['name']}")
        return

    if not click_download_original_file(driver):
        print(f"Could not find 'Download Original File' for: {file_item['name']}")
        return

    downloaded_path = wait_for_new_download(before_files, timeout=90)
    if not downloaded_path:
        print(f"Timed out waiting for download: {file_item['name']}")
        return

    move_download_to_course_folder(
        downloaded_path=downloaded_path,
        course_folder=course_folder,
        desired_name=file_item["name"],
        manifest=manifest,
        source_id=source_id
    )


def close_blackboard_help_if_open(driver):
    try:
        buttons = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Close")]')
        for btn in buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                break
            except Exception:
                continue
    except Exception:
        pass


def scrape_current_course_page(driver):
    close_blackboard_help_if_open(driver)

    course_name = detect_course_name(driver)
    print(f"Detected course: {course_name}")

    course_folder = os.path.join(COURSES_BASE_FOLDER, course_name)
    os.makedirs(course_folder, exist_ok=True)

    manifest = load_manifest(course_folder)

    scroll_to_bottom(driver)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    expand_all_sections(driver)
    scroll_to_bottom(driver)
    time.sleep(2)

    files = collect_visible_file_items(driver)
    print(f"\nFound {len(files)} PDF/PPT/PPTX items\n")

    for item in files:
        download_one_file_via_browser(driver, course_folder, item, manifest)

    save_manifest(course_folder, manifest)


def main():
    os.makedirs(COURSES_BASE_FOLDER, exist_ok=True)
    clear_browser_downloads_folder()

    driver = create_driver()
    driver.get(BLACKBOARD_URL)

    input("Log in, open ONE course, click Content, make sure the page is visible, then press ENTER... ")

    scrape_current_course_page(driver)

    while True:
        choice = input(
            "\nType ENTER to scrape another course page, or type q then ENTER to quit: "
        ).strip().lower()

        if choice == "q":
            break

        input("Open the next course Content page, then press ENTER... ")
        scrape_current_course_page(driver)

    print("\nDone.")
    input("Press ENTER to close browser... ")
    driver.quit()


if __name__ == "__main__":
    main()