import os
import json
import subprocess
from typing import List, Tuple, Union
import xml.etree.ElementTree as ET
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.chat_models import ChatOpenAI
from langchain.schema import AgentAction, AgentFinish
from langchain.prompts import StringPromptTemplate
from langchain.memory import ConversationBufferMemory

# --- Tools definitions


# === Tool 1: Scan workspace for pom.xml files ===
class FileScannerTool(Tool):
    name = "file_scanner"
    description = "Scan workspace directory recursively and list all pom.xml files."

    def _run(self, workspace_dir: str) -> List[str]:
        pom_files = []
        for root, dirs, files in os.walk(workspace_dir):
            if "pom.xml" in files:
                pom_files.append(os.path.join(root, "pom.xml"))
        return pom_files


# === Tool 2: Analyze Maven pom.xml to extract modules, dependencies, plugins ===
class PomAnalyzerTool(Tool):
    name = "pom_analyzer"
    description = "Analyze a pom.xml file and return its modules, dependencies, plugins in a dict."

    def _run(self, pom_path: str) -> dict:
        try:
            tree = ET.parse(pom_path)
            root = tree.getroot()
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}

            modules = []
            modules_tag = root.find("m:modules", ns)
            if modules_tag:
                modules = [m.text for m in modules_tag.findall("m:module", ns)]

            dependencies = []
            deps_tag = root.find("m:dependencies", ns)
            if deps_tag:
                for dep in deps_tag.findall("m:dependency", ns):
                    groupId = dep.find("m:groupId", ns).text
                    artifactId = dep.find("m:artifactId", ns).text
                    version = (
                        dep.find("m:version", ns).text
                        if dep.find("m:version", ns) is not None
                        else None
                    )
                    dependencies.append(
                        {
                            "groupId": groupId,
                            "artifactId": artifactId,
                            "version": version,
                        }
                    )

            plugins = []
            plugins_tag = root.find("m:build/m:plugins", ns)
            if plugins_tag:
                for plugin in plugins_tag.findall("m:plugin", ns):
                    groupId = (
                        plugin.find("m:groupId", ns).text
                        if plugin.find("m:groupId", ns) is not None
                        else None
                    )
                    artifactId = plugin.find("m:artifactId", ns).text
                    version = (
                        plugin.find("m:version", ns).text
                        if plugin.find("m:version", ns) is not None
                        else None
                    )
                    plugins.append(
                        {
                            "groupId": groupId,
                            "artifactId": artifactId,
                            "version": version,
                        }
                    )

            return {
                "modules": modules,
                "dependencies": dependencies,
                "plugins": plugins,
            }
        except Exception as e:
            return {"error": str(e)}


# === Tool 3: Generate initial build.gradle content from analyzed Maven data ===
class GradleGeneratorTool(Tool):
    name = "gradle_generator"
    description = "Generate a build.gradle file content from Maven project analysis."

    def _run(self, analysis: dict) -> str:
        # Simple example conversion, extend as needed
        dependencies = analysis.get("dependencies", [])
        plugins = analysis.get("plugins", [])

        lines = []
        lines.append("plugins {")
        lines.append("    id 'java'")
        lines.append("}")
        lines.append("\nrepositories {")
        lines.append("    mavenCentral()")
        lines.append("}\n")

        lines.append("dependencies {")
        for dep in dependencies:
            group = dep.get("groupId", "")
            artifact = dep.get("artifactId", "")
            version = dep.get("version", "")
            if version:
                lines.append(f"    implementation '{group}:{artifact}:{version}'")
            else:
                lines.append(f"    implementation '{group}:{artifact}'")
        lines.append("}")

        return "\n".join(lines)


# === Tool 4: Generate settings.gradle for multi-module projects ===
class SettingsGradleGeneratorTool(Tool):
    name = "settings_gradle_generator"
    description = "Generate settings.gradle file content listing all modules."

    def _run(self, modules: List[str]) -> str:
        lines = [f"include '{module}'" for module in modules]
        return "\n".join(lines)


# === Tool 5: Write gradle files to disk ===
class GradleWriterTool(Tool):
    name = "gradle_writer_tool"
    description = "Write provided gradle file content (build.gradle or settings.gradle) in project directory."

    def _run(self, args: dict) -> str:
        """
        args: dict with keys:
          - 'file_name': e.g., 'build.gradle' or 'settings.gradle'
          - 'content': string content to write
          - 'project_dir': base dir to write file into
        """
        file_name = args.get("file_name")
        content = args.get("content")
        project_dir = args.get("project_dir")
        if not file_name or not content or not project_dir:
            return "❌ Missing arguments for writing gradle file."

        # Ensure file_name and project_dir are strings and not None
        if not isinstance(file_name, str) or not isinstance(project_dir, str):
            return "❌ file_name and project_dir must be strings."

        path = os.path.join(project_dir, file_name)
        try:
            with open(path, "w") as f:
                f.write(content)
            return f"✅ Successfully wrote {file_name} at {path}"
        except Exception as e:
            return f"❌ Failed to write {file_name}: {e}"


# === Tool 6: Run gradle build commands ===
class GradleBuildTool(Tool):
    name = "gradle_build_tool"
    description = (
        "Run Gradle commands like clean build and return output and success/failure."
    )

    def _run(self, args: dict) -> str:
        """
        args: dict with keys:
          - 'project_dir': project root directory
          - 'command': gradle command string e.g., 'clean build'
        """
        project_dir = args.get("project_dir")
        command = args.get("command", "clean build")
        if not project_dir or not os.path.isdir(project_dir):
            return "❌ Invalid project directory."

        try:
            cmd = ["gradle"] + command.split()
            result = subprocess.run(
                cmd, cwd=project_dir, capture_output=True, text=True, timeout=300
            )
            output = result.stdout + "\n" + result.stderr
            if result.returncode == 0 and "BUILD SUCCESSFUL" in output:
                return f"✅ Gradle build succeeded."
            else:
                return f"❌ Gradle build failed:\n{output}\n\n💡 Suggestions: Analyze errors and suggest fixes."
        except Exception as e:
            return f"❌ Gradle build execution error: {e}"


# === Helper function to read build.gradle content ===
def read_build_gradle(project_dir: str) -> str:
    path = os.path.join(project_dir, "build.gradle")
    if os.path.isfile(path):
        with open(path, "r") as f:
            return f.read()
    return ""


# === GPT/Gemini call to fix build.gradle file ===
def ask_gpt_to_fix_gradle_files(error_output: str, current_build_gradle: str) -> str:
    llm = ChatOpenAI(model="gemini", temperature=0)
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
    fixed_gradle_code = llm.predict(prompt)
    return fixed_gradle_code


# === Iterative Gradle fix loop ===
def iterative_gradle_fix(project_dir: str, max_attempts: int = 3) -> bool:
    gradle_build_tool = GradleBuildTool()
    gradle_writer_tool = GradleWriterTool()

    for attempt in range(1, max_attempts + 1):
        print(f"🔄 Attempt {attempt} to run 'gradle clean build' ...")
        result = gradle_build_tool._run(
            {"project_dir": project_dir, "command": "clean build"}
        )

        if "✅ Gradle build succeeded" in result:
            print("🎉 Build succeeded!")
            return True
        else:
            try:
                error_output = result.split("❌ Gradle build failed:\n")[1].split(
                    "\n\n💡 Suggestions:"
                )[0]
            except Exception:
                error_output = result

            print(f"❌ Build failed. Analyzing errors and applying fixes...\n")
            current_build_gradle = read_build_gradle(project_dir)

            fixed_gradle_code = ask_gpt_to_fix_gradle_files(
                error_output, current_build_gradle
            )

            write_result = gradle_writer_tool._run(
                {
                    "file_name": "build.gradle",
                    "content": fixed_gradle_code,
                    "project_dir": project_dir,
                }
            )
            print(write_result)
            print("✅ Applied fixes. Re-running build...\n")

    print("⚠️ Max attempts reached. Build still failing.")
    return False


# --- Prompt with strict JSON response instruction ---


class MigrationPromptTemplate:
    def format(self, **kwargs) -> str:
        user_input = kwargs.get("input", "")
        agent_scratchpad = kwargs.get("agent_scratchpad", "")

        return f"""
You are an AI agent specialized in migrating Maven projects to Gradle.

Workspace input:
{user_input}

Previous actions and observations:
{agent_scratchpad}

Instructions:
Respond ONLY in JSON with ONE of the following:

1) To call a tool:

{{
  "tool_name": "<tool_name>",
  "tool_input": <tool_input>
}}

(tool_input can be a string or JSON object)

2) To finish:

{{
  "final_answer": "<your final summary>"
}}

Available tools: file_scanner, pom_analyzer, gradle_generator, gradle_writer, settings_gradle_generator, gradle_build_tool.

Example:

{{"tool_name": "file_scanner", "tool_input": "/path/to/project"}}

{{"final_answer": "Migration complete. Gradle build files generated."}}

---

What do you want to do next?
"""


# --- The smarter agent ---


class MavenToGradleAgent(LLMSingleActionAgent):
    def __init__(self):
        llm = ChatOpenAI(model="gemini", temperature=0)
        prompt = MigrationPromptTemplate()
        super().__init__(llm=llm, prompt=prompt)

        self.tools = {
            "file_scanner": FileScannerTool(),
            "pom_analyzer": PomAnalyzerTool(),
            "gradle_generator": GradleGeneratorTool(),
            "gradle_writer": GradleWriterTool(),
            "settings_gradle_generator": SettingsGradleGeneratorTool(),
            "gradle_build_tool": GradleBuildTool(),
        }

    def plan(
        self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs
    ) -> Union[AgentAction, AgentFinish]:
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += f"Action: {action.tool}\nAction Input: {action.tool_input}\nObservation: {observation}\n"

        user_input = kwargs.get("input", "")
        project_dir = kwargs.get("project_dir", "")

        prompt = self.prompt.format(input=user_input, agent_scratchpad=thoughts)
        response = self.llm.predict(prompt)

        try:
            parsed = json.loads(response.strip())

            if "final_answer" in parsed:
                return AgentFinish(
                    return_values={"output": parsed["final_answer"]}, log=response
                )

            tool_name = parsed.get("tool_name")
            tool_input = parsed.get("tool_input")

            if tool_name not in self.tools:
                return AgentFinish(
                    return_values={"output": f"Error: Unknown tool '{tool_name}'."},
                    log=response,
                )

            if (
                isinstance(tool_input, dict)
                and "project_dir" not in tool_input
                and project_dir
            ):
                tool_input["project_dir"] = project_dir

            return AgentAction(tool=tool_name, tool_input=tool_input, log=response)

        except json.JSONDecodeError:
            if "final answer:" in response.lower():
                answer = response.split("final answer:")[-1].strip()
                return AgentFinish(return_values={"output": answer}, log=response)
            return AgentFinish(
                return_values={"output": "Could not parse agent response."},
                log=response,
            )

    def run_tool(self, action: AgentAction) -> str:
        tool = self.tools.get(action.tool)
        if not tool:
            return f"Tool {action.tool} not found."
        return tool._run(action.tool_input)


# --- Safety helpers to avoid infinite loops ---


def has_repeated_steps(steps, repeat_threshold=3):
    if len(steps) < repeat_threshold:
        return False
    last_actions = steps[-repeat_threshold:]
    first_action = last_actions[0]
    return all(
        a.tool == first_action.tool and a.tool_input == first_action.tool_input
        for a, _ in last_actions
    )


# --- Main runner with max step count and repeated step detection ---

MAX_STEPS = 10
REPEAT_THRESHOLD = 3


def run_agent():
    agent = MavenToGradleAgent()
    intermediate_steps = []

    # Get project directory from environment or use default
    project_dir = os.getenv("MAVEN_PROJECT_DIR", os.path.abspath("./maven-project"))
    if not os.path.exists(project_dir):
        print(f"Error: Project directory not found: {project_dir}")
        return

    user_input = f"Start migration for project directory: {project_dir}"

    for step in range(MAX_STEPS):
        action_or_finish = agent.plan(
            intermediate_steps, input=user_input, project_dir=project_dir
        )

        if isinstance(action_or_finish, AgentFinish):
            print(f"Agent Finished: {action_or_finish.return_values['output']}")
            return

        observation = agent.run_tool(action_or_finish)
        print(f"Step {step + 1}, Tool '{action_or_finish.tool}' output: {observation}")

        intermediate_steps.append((action_or_finish, observation))

        if has_repeated_steps(intermediate_steps, REPEAT_THRESHOLD):
            print("Detected repeated actions. Stopping to avoid infinite loop.")
            return

    print(f"Maximum steps ({MAX_STEPS}) reached. Stopping execution.")


if __name__ == "__main__":
    run_agent()
