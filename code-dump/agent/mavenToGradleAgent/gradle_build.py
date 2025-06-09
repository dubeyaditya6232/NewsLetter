import subprocess
import platform
import logging


def run_gradle_clean_build(gradle_dir):
    is_windows = platform.system().lower().startswith("win")
    gradle_cmd = ["gradle"]
    build_proc = subprocess.run(
        gradle_cmd + ["clean", "build"],
        cwd=gradle_dir,
        capture_output=True,
        text=True,
        shell=is_windows,
    )
    build_output = build_proc.stdout + "\n" + build_proc.stderr
    return build_proc.returncode, build_output


def generate_gradle_wrapper(project_dir, gradle_cmd=None):
    """
    Generates Gradle wrapper files in the project directory.
    gradle_cmd: list, e.g. ['gradle', 'wrapper']
    """
    is_windows = platform.system().lower().startswith("win")
    logger = logging.getLogger(__name__)
    logger.info("Generating Gradle wrapper files...")
    print("⚙️  Generating Gradle wrapper files...")
    if gradle_cmd is None:
        gradle_cmd = ["gradle", "wrapper"]
    result = subprocess.run(
        gradle_cmd,
        cwd=project_dir,
        capture_output=True,
        text=True,
        shell=is_windows,
    )
    if result.returncode == 0:
        print("✅ Gradle wrapper files generated.")
        logger.info("Gradle wrapper files generated.")
    else:
        print("❌ Failed to generate Gradle wrapper files.")
        logger.error(f"Failed to generate Gradle wrapper files: {result.stderr}")
