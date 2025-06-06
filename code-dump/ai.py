import openai
import xml.etree.ElementTree as ET
import os
import shutil
import subprocess
from typing import List, Dict, Optional, Tuple
from main import MavenToGradleConverter 

class GradleConverterAgent:
    def __init__(self, project_path: str, openai_api_key: str):
        self.project_path = project_path
        self.converter = MavenToGradleConverter(project_path)
        self.max_attempts = 3
        openai.api_key = openai_api_key

    def ask_llm(self, error_output: str) -> Optional[Dict]:
        """Ask LLM for help with Gradle build error"""
        prompt = f"""
        I'm converting a Maven project to Gradle and encountered this build error:

        {error_output}

        Please analyze this error and provide:
        1. The root cause
        2. The exact fix needed in build.gradle
        3. Any additional configuration needed

        Format your response as JSON:
        {{
            "cause": "brief explanation of the root cause",
            "fix": "the exact gradle configuration needed",
            "location": "where to add/modify the fix (e.g., 'plugins block', 'dependencies block')",
            "additional_steps": ["any additional steps needed"]
        }}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in Gradle builds and Maven to Gradle migration."},
                {"role": "user", "content": prompt}
            ]
        )

        try:
            return eval(response.choices[0].message.content)
        except:
            print("Could not parse LLM response")
            return None

    def apply_llm_fix(self, fix_info: Dict) -> bool:
        """Apply the fix suggested by LLM"""
        if not fix_info:
            return False

        gradle_file = os.path.join(self.project_path, "build.gradle")
        with open(gradle_file, 'r') as f:
            content = f.read()

        # Apply the fix based on location
        if fix_info['location'] == 'plugins block':
            content = self._fix_plugins_block(content, fix_info['fix'])
        elif fix_info['location'] == 'dependencies block':
            content = self._fix_dependencies_block(content, fix_info['fix'])
        elif fix_info['location'] == 'repositories block':
            content = self._fix_repositories_block(content, fix_info['fix'])
        else:
            # Add to end of file if location not specified
            content += f"\n{fix_info['fix']}\n"

        # Write back the modified content
        with open(gradle_file, 'w') as f:
            f.write(content)

        # Execute any additional steps
        for step in fix_info.get('additional_steps', []):
            try:
                subprocess.run(step, shell=True, cwd=self.project_path, check=True)
            except Exception as e:
                print(f"Error executing step '{step}': {str(e)}")

        return True

    def _fix_plugins_block(self, content: str, fix: str) -> str:
        """Fix plugins block in build.gradle"""
        plugin_section_end = content.find('}', content.find('plugins {')) + 1
        return content[:plugin_section_end-1] + f"\n{fix}\n" + content[plugin_section_end:]

    def _fix_dependencies_block(self, content: str, fix: str) -> str:
        """Fix dependencies block in build.gradle"""
        deps_section_end = content.find('}', content.find('dependencies {')) + 1
        return content[:deps_section_end-1] + f"\n{fix}\n" + content[deps_section_end:]

    def _fix_repositories_block(self, content: str, fix: str) -> str:
        """Fix repositories block in build.gradle"""
        repos_section_end = content.find('}', content.find('repositories {')) + 1
        return content[:repos_section_end-1] + f"\n{fix}\n" + content[repos_section_end:]

    def run(self):
        """Main execution flow"""
        print("Starting Maven to Gradle conversion process...")
        
        try:
            # 1. Convert Maven to Gradle
            self.converter.convert()
            
            # 2. Attempt build and fix errors
            attempt = 1
            while attempt <= self.max_attempts:
                print(f"\nAttempting gradle build (attempt {attempt}/{self.max_attempts})...")
                
                # Run gradle build
                process = subprocess.run(
                    ["gradle", "clean", "build"],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True
                )
                
                if process.returncode == 0:
                    print("Build successful!")
                    return True
                
                print(f"Build failed. Consulting LLM for analysis...")
                error_output = process.stderr or process.stdout
                
                # Get fix from LLM
                fix_info = self.ask_llm(error_output)
                if fix_info:
                    print(f"Root cause: {fix_info['cause']}")
                    print("Applying suggested fix...")
                    if self.apply_llm_fix(fix_info):
                        print("Fix applied, retrying build...")
                        attempt += 1
                    else:
                        print("Could not apply the suggested fix.")
                        break
                else:
                    print("Could not get a valid fix suggestion from LLM.")
                    break
            
            return False
                
        except Exception as e:
            print(f"Error during conversion: {str(e)}")
            return False

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python agent.py <project_path>")
        sys.exit(1)

    # Get OpenAI API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        sys.exit(1)

    agent = GradleConverterAgent(sys.argv[1], api_key)
    agent.run()