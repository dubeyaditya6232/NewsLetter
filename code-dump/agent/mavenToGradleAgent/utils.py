import os
import logging
import subprocess


def safe_write_file(path: str, content: str) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to write file {path}: {e}")
        return False


def read_build_gradle(project_dir: str) -> str:
    path = os.path.join(project_dir, "build.gradle")
    if os.path.isfile(path):
        with open(path, "r") as f:
            return f.read()
    return ""


def verify_tools_installed() -> bool:
    """Verify that required tools (Maven, Gradle) are installed."""
    try:
        subprocess.run(
            ["mvn", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=True,
        )
        subprocess.run(
            ["gradle", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.getLogger(__name__).error(
            f"Maven or Gradle not found. Please install required tools. Error: {e}"
        )
        return False


def strip_markdown_code_block(text: str) -> str:
    """
    Removes leading/trailing triple backtick code block markers from a string.
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def write_gradle_files_from_dict(gradle_dir, gradle_dict):
    gradle_files_written = False
    if not isinstance(gradle_dict, dict):
        return False
    build_gradle = gradle_dict.get("build_gradle")
    settings_gradle = gradle_dict.get("settings_gradle")
    if build_gradle:
        safe_write_file(os.path.join(gradle_dir, "build.gradle"), build_gradle)
        print("✅ build.gradle written.")
        gradle_files_written = True
    if settings_gradle:
        safe_write_file(os.path.join(gradle_dir, "settings.gradle"), settings_gradle)
        print("✅ settings.gradle written.")
        gradle_files_written = True
    return gradle_files_written


def gradle_build_has_errors(returncode, build_output):
    """
    Returns True if the Gradle build failed, False if successful.
    """
    return returncode != 0 or "BUILD FAILED" in build_output
