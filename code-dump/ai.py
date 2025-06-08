import os
import json
import logging
import subprocess
from typing import List, Tuple, Union, Optional, Dict, Any
import xml.etree.ElementTree as ET
import shutil
from google import genai

# --- Tools definitions

# === Tool 1: Scan workspace for pom.xml files ===
# class FileScannerTool:
#     def __init__(self):
#         super().__init__()
#         self.name = "file_scanner"
#         self.description = (
#             "Scan workspace directory recursively and list all pom.xml files."
#         )
#
#     def _run(self, workspace_dir: str) -> List[str]:
#         pom_files = []
#         for root, dirs, files in os.walk(workspace_dir):
#             if "pom.xml" in files:
#                 pom_files.append(os.path.join(root, "pom.xml"))
#         return pom_files

# === Tool 2: Analyze Maven pom.xml to extract modules, dependencies, plugins ===
# class PomAnalyzerTool:
#     def __init__(self):
#         super().__init__()
#         self.name = "pom_analyzer"
#         self.description = "Analyze a pom.xml file and return its modules, dependencies, plugins in a dict."
#
#     def _run(self, pom_path: str) -> dict:
#         try:
#             tree = ET.parse(pom_path)
#             root = tree.getroot()
#             ns = {"m": "http://maven.apache.org/POM/4.0.0"}
#
#             modules = []
#             modules_tag = root.find("m:modules", ns)
#             if modules_tag:
#                 modules = [m.text for m in modules_tag.findall("m:module", ns)]
#
#             dependencies = []
#             deps_tag = root.find("m:dependencies", ns)
#             if deps_tag:
#                 for dep in deps_tag.findall("m:dependency", ns):
#                     groupId_elem = dep.find("m:groupId", ns)
#                     artifactId_elem = dep.find("m:artifactId", ns)
#                     version_elem = dep.find("m:version", ns)
#                     groupId = groupId_elem.text if groupId_elem is not None else None
#                     artifactId = (
#                         artifactId_elem.text if artifactId_elem is not None else None
#                     )
#                     version = version_elem.text if version_elem is not None else None
#                     dependencies.append(
#                         {
#                             "groupId": groupId,
#                             "artifactId": artifactId,
#                             "version": version,
#                         }
#                     )
#
#             plugins = []
#             plugins_tag = root.find("m:build/m:plugins", ns)
#             if plugins_tag is not None:
#                 for plugin in plugins_tag.findall("m:plugin", ns):
#                     groupId_elem = plugin.find("m:groupId", ns)
#                     artifactId_elem = plugin.find("m:artifactId", ns)
#                     version_elem = plugin.find("m:version", ns)
#                     groupId = groupId_elem.text if groupId_elem is not None else None
#                     artifactId = (
#                         artifactId_elem.text if artifactId_elem is not None else None
#                     )
#                     version = version_elem.text if version_elem is not None else None
#                     plugins.append(
#                         {
#                             "groupId": groupId,
#                             "artifactId": artifactId,
#                             "version": version,
#                         }
#                     )
#
#             return {
#                 "modules": modules,
#                 "dependencies": dependencies,
#                 "plugins": plugins,
#             }
#         except Exception as e:
#             return {"error": str(e)}

# === Tool 3: Generate initial build.gradle content from analyzed Maven data ===
# class GradleGeneratorTool:
#     def __init__(self):
#         super().__init__()
#         self.name = "gradle_generator"
#         self.description = (
#             "Generate a build.gradle file content from Maven project analysis."
#         )
#
#     def _run(self, analysis: dict) -> str:
#         dependencies = analysis.get("dependencies", [])
#         plugins = analysis.get("plugins", [])
#
#         # Default versions (could be improved by extracting from pom.xml in a real agent)
#         spring_boot_version = "3.2.6"
#         dependency_management_version = "1.1.4"
#         lombok_version = "1.18.32"
#         group = "com.wf.agent"
#         version = "0.0.1-SNAPSHOT"
#         source_compatibility = "17"
#
#         lines = []
#         lines.append("plugins {")
#         lines.append("    id 'java'")
#         lines.append(
#             f"    id 'org.springframework.boot' version '{spring_boot_version}'"
#         )
#         lines.append(
#             f"    id 'io.spring.dependency-management' version '{dependency_management_version}'"
#         )
#         lines.append("}")
#         lines.append("")
#         lines.append(f"group = '{group}'")
#         lines.append(f"version = '{version}'")
#         lines.append(f"sourceCompatibility = '{source_compatibility}'")
#         lines.append("")
#         lines.append("repositories {")
#         lines.append("    mavenCentral()")
#         lines.append("}")
#         lines.append("")
#         lines.append("dependencies {")
#         for dep in dependencies:
#             group_id = dep.get("groupId", "")
#             artifact = dep.get("artifactId", "")
#             dep_version = dep.get("version", "")
#             if artifact == "spring-boot-starter-web":
#                 lines.append(
#                     "    implementation 'org.springframework.boot:spring-boot-starter-web'"
#                 )
#             elif artifact == "spring-boot-devtools":
#                 lines.append(
#                     "    developmentOnly 'org.springframework.boot:spring-boot-devtools'"
#                 )
#             elif artifact == "lombok":
#                 lines.append(
#                     f"    compileOnly 'org.projectlombok:lombok:{lombok_version}'"
#                 )
#                 lines.append(
#                     f"    annotationProcessor 'org.projectlombok:lombok:{lombok_version}'"
#                 )
#             elif artifact == "spring-boot-starter-test":
#                 lines.append(
#                     "    testImplementation 'org.springframework.boot:spring-boot-starter-test'"
#                 )
#             elif artifact == "spring-security-test":
#                 lines.append(
#                     "    testImplementation 'org.springframework.security:spring-security-test'"
#                 )
#             else:
#                 # fallback for any other dependency
#                 if dep_version:
#                     lines.append(
#                         f"    implementation '{group_id}:{artifact}:{dep_version}'"
#                     )
#                 else:
#                     lines.append(f"    implementation '{group_id}:{artifact}'")
#         lines.append("}")
#         lines.append("")
#         lines.append("test {")
#         lines.append("    useJUnitPlatform()")
#         lines.append("}")
#         return "\n".join(lines)

# === Tool 4: Generate settings.gradle for multi-module projects ===
# class SettingsGradleGeneratorTool:
#     def __init__(self):
#         super().__init__()
#         self.name = "settings_gradle_generator"
#         self.description = "Generate settings.gradle file content listing all modules."
#
#     def _run(self, modules: List[str]) -> str:
#         lines = [f"include '{module}'" for module in modules]
#         return "\n".join(lines)

# === Tool 5: Write gradle files to disk ===
# class GradleWriterTool:
#     def __init__(self):
#         super().__init__()
#         self.name = "gradle_writer_tool"
#         self.description = "Write provided gradle file content (build.gradle or settings.gradle) in project directory."
#
#     def _run(self, args: dict) -> str:
#         """
#         args: dict with keys:
#           - 'file_name': e.g., 'build.gradle' or 'settings.gradle'
#           - 'content': string content to write
#           - 'project_dir': base dir to write file into
#         """
#         file_name = args.get("file_name")
#         content = args.get("content")
#         project_dir = args.get("project_dir")
#         if not file_name or not content or not project_dir:
#             return "❌ Missing arguments for writing gradle file."
#
#         # Ensure file_name and project_dir are strings and not None
#         if not isinstance(file_name, str) or not isinstance(project_dir, str):
#             return "❌ file_name and project_dir must be strings."
#
#         path = os.path.join(project_dir, file_name)
#         try:
#             if safe_write_file(path, content):
#                 return f"✅ Successfully wrote {file_name} at {path}"
#             return f"❌ Failed to write {file_name}"
#         except Exception as e:
#             logger.error(f"GradleWriterTool failed: {e}")
#             return f"❌ Failed to write {file_name}: {e}"


# === Helper function to safely write files ===
def safe_write_file(path: str, content: str) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to write file {path}: {e}")
        return False


# === Tool 6: Run gradle build commands ===
# class GradleBuildTool:
#     def __init__(self):
#         super().__init__()
#         self.name = "gradle_build_tool"
#         self.description = "Run Gradle commands like clean build and return output and success/failure."
#
#     def _run(self, args: dict) -> str:
#         """
#         args: dict with keys:
#           - 'project_dir': project root directory
#           - 'command': gradle command string e.g., 'clean build'
#         """
#         project_dir = args.get("project_dir")
#         command = args.get("command", "clean build")
#         if not project_dir or not os.path.isdir(project_dir):
#             return "❌ Invalid project directory."
#
#         try:
#             cmd = ["gradle"] + command.split()
#             result = subprocess.run(
#                 cmd, cwd=project_dir, capture_output=True, text=True, timeout=300
#             )
#             output = result.stdout + "\n" + result.stderr
#             if result.returncode == 0 and "BUILD SUCCESSFUL" in output:
#                 return f"✅ Gradle build succeeded."
#             else:
#                 return f"❌ Gradle build failed:\n{output}\n\n💡 Suggestions: Analyze errors and suggest fixes."
#         except Exception as e:
#             return f"❌ Gradle build execution error: {e}"


# === Tool 7: Cleanup Maven files after migration ===
# class MavenCleanupTool:
#     def __init__(self):
#         super().__init__()
#         self.name = "maven_cleanup"
#         self.description = "Backup and remove Maven configuration files after successful Gradle migration"
#
#     def _run(self, args: dict) -> str:
#         """
#         args: dict with keys:
#           - 'project_dir': project root directory
#           - 'backup': boolean, whether to keep backups (default True)
#         """
#         project_dir = args.get("project_dir")
#         keep_backup = args.get("backup", True)
#
#         if not project_dir or not os.path.isdir(project_dir):
#             return "❌ Invalid project directory"
#
#         try:
#             # Create backup directory
#             backup_dir = os.path.join(project_dir, "maven_backup")
#             os.makedirs(backup_dir, exist_ok=True)
#
#             # Files to backup/remove
#             maven_files = ["pom.xml", ".mvn", "mvnw", "mvnw.cmd"]
#
#             for item in maven_files:
#                 path = os.path.join(project_dir, item)
#                 if os.path.exists(path):
#                     if keep_backup:
#                         backup_path = os.path.join(backup_dir, item)
#                         if os.path.isdir(path):
#                             shutil.copytree(path, backup_path, dirs_exist_ok=True)
#                         else:
#                             shutil.copy2(path, backup_path)
#
#                     # Remove original
#                     if os.path.isdir(path):
#                         shutil.rmtree(path)
#                     else:
#                         os.remove(path)
#
#             return f"✅ Maven files {'backed up and ' if keep_backup else ''}removed"
#
#         except Exception as e:
#             logger.error(f"Failed to cleanup Maven files: {e}")
#             return f"❌ Cleanup failed: {e}"


# === Tool 8: LLM-based Gradle converter ===
class LLMGradleConverterTool:
    def __init__(self):
        super().__init__()
        self.name = "llm_gradle_converter"
        self.description = "Send pom.xml content to LLM and get build.gradle and settings.gradle as response."

    def _run(self, args: dict) -> dict:
        """
        args: dict with keys:
          - 'pom_path': path to pom.xml file
        Returns: dict with keys 'build_gradle' and 'settings_gradle'
        """
        pom_path = args.get("pom_path")
        if not pom_path or not os.path.isfile(pom_path):
            return {"error": "Invalid pom.xml path"}
        with open(pom_path, "r", encoding="utf-8") as f:
            pom_content = f.read()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"error": "GOOGLE_API_KEY environment variable not set"}
        client = genai.Client(api_key=api_key)
        prompt = (
            "You are an expert in build tool migration. "
            "Given the following Maven pom.xml, generate the equivalent Gradle build.gradle and settings.gradle files. "
            "Respond ONLY with a single valid JSON object with two fields: 'build_gradle' and 'settings_gradle', each containing the full file content as a string. No markdown, no explanation, no code block, no comments.\n"
            "\nHere is the pom.xml:\n"
            f"{pom_content}\n"
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        if hasattr(response, "text"):
            text = response.text
        else:
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception:
                text = str(response)
        # --- Fix: Strip markdown code block if present ---
        text = text.strip()
        if text.startswith("```"):
            # Remove the first line (``` or ```json)
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove the last line if it's a closing code block
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            parsed = json.loads(text)
            return parsed
        except Exception:
            return {"error": f"Could not parse LLM response. Raw: {text}"}


# === Helper function to read build.gradle content ===
def read_build_gradle(project_dir: str) -> str:
    path = os.path.join(project_dir, "build.gradle")
    if os.path.isfile(path):
        with open(path, "r") as f:
            return f.read()
    return ""


# === GPT/Gemini call to fix build.gradle file ===
def ask_gpt_to_fix_gradle_files(error_output: str, current_build_gradle: str) -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable not set")
    client = genai.Client(api_key=api_key)
    prompt = (
        "You are an expert Gradle build engineer.\n"
        "Given the following Gradle build error output and the current build.gradle file, "
        "please provide a corrected build.gradle file that fixes the errors.\n\n"
        "### Gradle build errors:\n"
        f"{error_output}\n\n"
        "### Current build.gradle:\n"
        f"{current_build_gradle}\n\n"
        "### Please provide the full corrected build.gradle file only, no explanation."
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    # The response object may have a .text or .candidates[0].content.parts[0].text depending on the API version
    if hasattr(response, "text"):
        return response.text
    try:
        return response.candidates[0].content.parts[0].text
    except Exception:
        return str(response)


# --- Prompt with strict JSON response instruction ---


class MigrationPromptTemplate:
    input_variables = ["input", "agent_scratchpad"]

    def format(self, **kwargs) -> str:
        user_input: str = kwargs.get("input", "")
        agent_scratchpad: str = kwargs.get("agent_scratchpad", "")

        return (
            "You are an AI agent specialized in migrating Maven projects to Gradle.\n"
            "\nWorkspace input:\n"
            f"{user_input}\n"
            "\nPrevious actions and observations:\n"
            f"{agent_scratchpad}\n"
            "\nINSTRUCTIONS (STRICT):\n"
            "Respond ONLY with a single valid JSON object, no markdown, no explanation, no extra text, no code block, no comments.\n"
            "Your response MUST be a single line of valid JSON.\n"
            "\nChoose ONE of the following formats:\n"
            "1) To call a tool:\n"
            '{"tool_name": "<tool_name>", "tool_input": <tool_input>}\n'
            "(tool_input can be a string or JSON object)\n"
            "2) To finish:\n"
            '{"final_answer": "<your final summary>"}\n'
            "\nAvailable tools: llm_gradle_converter.\n"
            "\nExample:\n"
            '{"tool_name": "llm_gradle_converter", "tool_input": {"pom_path": "/path/to/pom.xml"}}'
            '\n{"final_answer": "Migration complete. Gradle build files generated."}'
            "\n---\n"
            "What do you want to do next?"
        )


# --- The smarter agent ---


class MavenToGradleAgent:
    def __init__(self, model_name: str, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.tools = {
            # "file_scanner": FileScannerTool(),
            # "pom_analyzer": PomAnalyzerTool(),
            # "gradle_writer": GradleWriterTool(),
            # "gradle_build_tool": GradleBuildTool(),
            # "maven_cleanup": MavenCleanupTool(),
            # "gradle_health_check": GradleHealthCheckTool(),
            "llm_gradle_converter": LLMGradleConverterTool(),
        }

    def plan(self, intermediate_steps, **kwargs):
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += f"Action: {action['tool']}\nAction Input: {action['tool_input']}\nObservation: {observation}\n"
        user_input = kwargs.get("input", "")
        project_dir = kwargs.get("project_dir", "")
        prompt = MigrationPromptTemplate().format(
            input=user_input, agent_scratchpad=thoughts
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        # The response object may have a .text or .candidates[0].content.parts[0].text depending on the API version
        if hasattr(response, "text"):
            text = response.text
        else:
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception:
                text = str(response)
        print("Gemini raw response:", text)  # Debug: print raw LLM output
        try:
            parsed = json.loads(text.strip())
            if "final_answer" in parsed:
                return {"finish": True, "output": parsed["final_answer"]}
            tool_name = parsed.get("tool_name")
            tool_input = parsed.get("tool_input")
            if tool_name not in self.tools:
                return {"finish": True, "output": f"Error: Unknown tool '{tool_name}'."}
            if (
                isinstance(tool_input, dict)
                and "project_dir" not in tool_input
                and project_dir
            ):
                tool_input["project_dir"] = project_dir
            return {"finish": False, "tool": tool_name, "tool_input": tool_input}
        except Exception:
            return {
                "finish": True,
                "output": f"Could not parse agent response. Raw: {text}",
            }

    def run_tool(self, action):
        try:
            tool = self.tools.get(action["tool"])
            if not tool:
                return f"Tool {action['tool']} not found."
            tool_input = action["tool_input"]
            # Only LLMGradleConverterTool is available
            return tool._run(tool_input)
        except Exception as e:
            return f"Tool execution failed: {e}"


def generate_gradle_wrapper(project_dir, gradle_cmd=None):
    """
    Generates Gradle wrapper files in the project directory.
    gradle_cmd: list, e.g. ['gradle', 'wrapper']
    """
    import platform

    is_windows = platform.system().lower().startswith("win")
    logger.info("Generating Gradle wrapper files...")
    print("⚙️  Generating Gradle wrapper files...")
    if gradle_cmd is None:
        gradle_cmd = ["gradle", "wrapper"]
    result = subprocess.run(
        gradle_cmd,
        cwd=project_dir,
        capture_output=True,
        text=True,
        shell=is_windows,  # <-- THIS IS THE FIX
    )
    if result.returncode == 0:
        print("✅ Gradle wrapper files generated.")
        logger.info("Gradle wrapper files generated.")
    else:
        print("❌ Failed to generate Gradle wrapper files.")
        logger.error(f"Failed to generate Gradle wrapper files: {result.stderr}")


def backup_and_remove_maven_files(project_dir):
    """
    Backs up and removes Maven files from the project directory.
    """
    logger.info("Backing up and removing Maven files...")
    print("🗃️  Backing up and removing Maven files...")
    backup_dir = os.path.join(project_dir, "maven_backup")
    os.makedirs(backup_dir, exist_ok=True)
    maven_files = ["pom.xml", ".mvn", "mvnw", "mvnw.cmd"]
    for item in maven_files:
        path = os.path.join(project_dir, item)
        if os.path.exists(path):
            backup_path = os.path.join(backup_dir, item)
            if os.path.isdir(path):
                shutil.copytree(path, backup_path, dirs_exist_ok=True)
                shutil.rmtree(path)
            else:
                shutil.copy2(path, backup_path)
                os.remove(path)
    print("✅ Maven files backed up and removed.")
    logger.info("Maven files backed up and removed.")


# --- Main runner with max step count and repeated step detection ---

MAX_STEPS = 10
REPEAT_THRESHOLD = 3


def run_agent():
    try:
        if not verify_tools_installed():
            return
        import sys

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY environment variable not set")
            return
        model_name = "gemini-2.0-flash"  # Use the correct model name for the new API
        agent = MavenToGradleAgent(model_name, api_key)
        intermediate_steps = []
        if len(sys.argv) > 1:
            project_dir = os.path.abspath(sys.argv[1])
        else:
            project_dir = os.getenv("MAVEN_PROJECT_DIR")
            if not project_dir:
                project_dir = os.path.abspath("./maven-project")
                logger.warning(
                    f"MAVEN_PROJECT_DIR not set, using default: {project_dir}"
                )
        if not os.path.exists(project_dir):
            logger.error(f"Project directory not found: {project_dir}")
            return
        # Use the directory provided by the user directly for gradle operations
        gradle_dir = project_dir
        if not os.path.isdir(gradle_dir):
            logger.error(f"Gradle project directory not found: {gradle_dir}")
            return
        if not os.path.isfile(os.path.join(gradle_dir, "pom.xml")):
            logger.error(f"No pom.xml found in {gradle_dir}")
            return
        user_input = f"Start migration for project directory: {gradle_dir}"
        result = None
        MAX_STEPS = 10
        REPEAT_THRESHOLD = 3

        def has_repeated_steps(steps, repeat_threshold=3):
            if len(steps) < repeat_threshold:
                return False
            last_actions = steps[-repeat_threshold:]
            first_action = last_actions[0]
            return all(
                a[0]["tool"] == first_action[0]["tool"]
                and a[0]["tool_input"] == first_action[0]["tool_input"]
                for a in last_actions
            )

        gradle_files_written = False
        for step in range(MAX_STEPS):
            action_or_finish = agent.plan(
                intermediate_steps, input=user_input, project_dir=gradle_dir
            )
            if action_or_finish["finish"]:
                result = action_or_finish["output"]
                # --- Write gradle files if LLM response contains them ---
                if isinstance(result, dict):
                    build_gradle = result.get("build_gradle")
                    settings_gradle = result.get("settings_gradle")
                    if build_gradle:
                        safe_write_file(
                            os.path.join(gradle_dir, "build.gradle"), build_gradle
                        )
                        print("✅ build.gradle written.")
                        gradle_files_written = True
                    if settings_gradle:
                        safe_write_file(
                            os.path.join(gradle_dir, "settings.gradle"),
                            settings_gradle,
                        )
                        print("✅ settings.gradle written.")
                        gradle_files_written = True
                print(f"Agent Finished: {result}")
                break
            observation = agent.run_tool(action_or_finish)
            # --- Write gradle files if LLM response contains them ---
            if isinstance(observation, dict):
                build_gradle = observation.get("build_gradle")
                settings_gradle = observation.get("settings_gradle")
                if build_gradle:
                    safe_write_file(
                        os.path.join(gradle_dir, "build.gradle"), build_gradle
                    )
                    print("✅ build.gradle written.")
                    gradle_files_written = True
                if settings_gradle:
                    safe_write_file(
                        os.path.join(gradle_dir, "settings.gradle"), settings_gradle
                    )
                    print("✅ settings.gradle written.")
                    gradle_files_written = True
            print(
                f"Step {step + 1}, Tool '{action_or_finish['tool']}' output: {observation}"
            )
            intermediate_steps.append((action_or_finish, observation))
            if has_repeated_steps(intermediate_steps, REPEAT_THRESHOLD):
                print("Detected repeated actions. Stopping to avoid infinite loop.")
                return

        # --- Always run gradle build, generate wrapper, and cleanup if gradle files were written ---
        if gradle_files_written:
            logger.info("Agent is running 'gradle clean build' to check for errors...")
            print("🚀 Running 'gradle clean build' to check for errors...")
            print(f"[DEBUG] Running gradle build in directory: {gradle_dir}")
            import subprocess
            import platform

            is_windows = platform.system().lower().startswith("win")

            # Always use 'gradle' command with shell=is_windows for all gradle operations
            gradle_cmd = ["gradle"]

            # Generate Gradle wrapper (optional, but always try for completeness)
            print("⚙️  Generating Gradle wrapper files (if not present)...")
            try:
                result = subprocess.run(
                    gradle_cmd + ["wrapper"],
                    cwd=gradle_dir,
                    capture_output=True,
                    text=True,
                    shell=is_windows,
                )
                if result.returncode != 0:
                    print("❌ Failed to generate Gradle wrapper. Output:")
                    print(result.stdout)
                    print(result.stderr)
                    # return
                else:
                    print("✅ Gradle wrapper generated (or already present).")
            except FileNotFoundError:
                print(
                    "❌ Gradle is not installed or not in PATH. Please install Gradle or add it to your PATH."
                )
                logger.error(
                    "Gradle is not installed or not in PATH. Please install Gradle or add it to your PATH."
                )
                return

            # Run gradle clean build
            build_proc = subprocess.run(
                gradle_cmd + ["clean", "build"],
                cwd=gradle_dir,
                capture_output=True,
                text=True,
                shell=is_windows,
            )
            build_output = build_proc.stdout + "\n" + build_proc.stderr
            print(f"[DEBUG] Gradle build return code: {build_proc.returncode}")
            print(f"[DEBUG] Gradle build output:\n{build_output}")
            logger.info(f"[DEBUG] Gradle build return code: {build_proc.returncode}")
            logger.info(f"[DEBUG] Gradle build output:\n{build_output}")
            # Debug: Confirm we reach the error check
            print("[DEBUG] Checking if build failed to trigger LLM fix...")
            if build_proc.returncode != 0 or "BUILD FAILED" in build_output:
                print(
                    "❌ Gradle build failed. Attempting to fix build.gradle using LLM..."
                )
                logger.info(
                    "Invoking LLM to fix build.gradle due to Gradle build failure..."
                )
                from pathlib import Path

                # Read current build.gradle
                with open(
                    os.path.join(gradle_dir, "build.gradle"),
                    "r",
                    encoding="utf-8",
                ) as f:
                    current_build_gradle = f.read()
                # Use ask_gpt_to_fix_gradle_files to get a fixed build.gradle
                fixed_gradle = ask_gpt_to_fix_gradle_files(
                    build_output, current_build_gradle
                )
                # --- Strip markdown code block if present ---
                fixed_gradle = fixed_gradle.strip()
                if fixed_gradle.startswith("```"):
                    lines = fixed_gradle.splitlines()
                    # Remove the first line (``` or ```gradle)
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    # Remove the last line if it's a closing code block
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    fixed_gradle = "\n".join(lines).strip()
                # Overwrite build.gradle
                with open(
                    os.path.join(gradle_dir, "build.gradle"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(fixed_gradle)
                print(
                    "✅ build.gradle fixed and written. Re-running 'gradle clean build'..."
                )
                build_proc2 = subprocess.run(
                    gradle_cmd + ["clean", "build"],
                    cwd=gradle_dir,
                    capture_output=True,
                    text=True,
                    shell=is_windows,
                )
                build_output2 = build_proc2.stdout + "\n" + build_proc2.stderr
                if build_proc2.returncode == 0 and "BUILD SUCCESSFUL" in build_output2:
                    print("🎉 Gradle build succeeded after fix!")
                    generate_gradle_wrapper(gradle_dir, gradle_cmd + ["wrapper"])
                    backup_and_remove_maven_files(gradle_dir)
                else:
                    print(
                        "❌ Gradle build still failed after fix. Please check build.gradle and errors below:"
                    )
                    print(build_output2)
            else:
                print("🎉 Gradle build succeeded!")
                generate_gradle_wrapper(gradle_dir, gradle_cmd + ["wrapper"])
                backup_and_remove_maven_files(gradle_dir)
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise


# Verify that required tools (Maven, Gradle) are installed
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
        logger.error(
            f"Maven or Gradle not found. Please install required tools. Error: {e}"
        )
        return False


if __name__ == "__main__":
    # Set up logging before any logger usage
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Add check for Google API key
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY environment variable not set")
        exit(1)

    logger.info("Starting Maven to Gradle migration agent...")
    try:
        run_agent()
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
