import os
import json
import logging
import sys
import xml.etree.ElementTree as ET
import shutil
from google import genai
import platform
from mavenToGradleAgent.gradle_build import (
    run_gradle_clean_build,
    generate_gradle_wrapper,
)
from mavenToGradleAgent.tools import LLMGradleConverterTool
from mavenToGradleAgent.utils import (
    verify_tools_installed,
    safe_write_file,
    read_build_gradle,
    strip_markdown_code_block,
    write_gradle_files_from_dict,
    gradle_build_has_errors,
)


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
                gradle_files_written |= write_gradle_files_from_dict(gradle_dir, result)
                print(f"Agent Finished: {result}")
                break
            observation = agent.run_tool(action_or_finish)
            gradle_files_written |= write_gradle_files_from_dict(
                gradle_dir, observation
            )
            print(
                f"Step {step + 1}, Tool '{action_or_finish['tool']}' output: {observation}"
            )
            intermediate_steps.append((action_or_finish, observation))
            if has_repeated_steps(intermediate_steps, REPEAT_THRESHOLD):
                print("Detected repeated actions. Stopping to avoid infinite loop.")
                return

        # --- Always run gradle build, generate wrapper, and cleanup if gradle files were written ---
        if gradle_files_written:
            generate_gradle_wrapper(gradle_dir, ["gradle", "wrapper"])
            logger.info("Agent is running 'gradle clean build' to check for errors...")
            print(f"[DEBUG] Running gradle build in directory: {gradle_dir}")

            # Try gradle clean build, and fix up to 5 times if it fails
            max_attempts = 5
            attempt = 0
            build_success = False
            build_output = ""
            while attempt < max_attempts:
                returncode, build_output = run_gradle_clean_build(gradle_dir)
                msg = f"[DEBUG] Gradle build attempt {attempt+1} return code: {returncode}"
                print(msg)
                logger.info(msg)
                logger.info(
                    f"[DEBUG] Gradle build output (attempt {attempt+1}):\n{build_output}"
                )
                if not gradle_build_has_errors(returncode, build_output):
                    build_success = True
                    break
                print(
                    f"❌ Gradle build failed on attempt {attempt+1}. Attempting to fix build.gradle using LLM..."
                )
                logger.info(
                    f"Invoking LLM to fix build.gradle (attempt {attempt+1})..."
                )
                with open(
                    os.path.join(gradle_dir, "build.gradle"), "r", encoding="utf-8"
                ) as f:
                    current_build_gradle = f.read()
                fixed_gradle = ask_gpt_to_fix_gradle_files(
                    build_output, current_build_gradle
                )
                fixed_gradle = strip_markdown_code_block(fixed_gradle)
                safe_write_file(os.path.join(gradle_dir, "build.gradle"), fixed_gradle)
                print(
                    f"✅ build.gradle fixed and written (attempt {attempt+1}). Re-running 'gradle clean build'..."
                )
                attempt += 1
            if build_success:
                print("🎉 Gradle build succeeded after fix!")
                backup_and_remove_maven_files(gradle_dir)
            else:
                print(
                    f"❌ Gradle build still failed after {max_attempts} attempts. Human intervention required."
                )
                logger.error(
                    f"Tried to fix build.gradle {max_attempts} times, still failing. Human intervention required. Last build output:\n{build_output}"
                )
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise


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
