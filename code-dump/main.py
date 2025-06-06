import xml.etree.ElementTree as ET
import os
import shutil
from typing import List, Dict, Optional
import subprocess


class MavenToGradleConverter:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.pom_file = os.path.join(project_path, "pom.xml")
        self.modules = []
        self.parent_info = None

    def _parse_parent(self, root) -> Optional[Dict]:
        """Parse parent pom information"""
        parent = root.find("parent")
        if parent is not None:
            return {
                "group": self._find_element(parent, "groupId"),
                "artifact": self._find_element(parent, "artifactId"),
                "version": self._find_element(parent, "version"),
            }
        return None

    def _parse_modules(self, root) -> List[str]:
        """Parse module definitions from the parent pom.xml"""
        modules = []
        modules_elem = root.find("modules")
        if modules_elem is not None:
            for module in modules_elem.findall("module"):
                if module.text:
                    modules.append(module.text)
        return modules

    def parse_pom(self) -> Dict:
        tree = ET.parse(self.pom_file)
        root = tree.getroot()

        # Remove namespace for easier parsing
        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

        # Parse modules if this is the parent pom
        self.modules = self._parse_modules(root)

        project_info = {
            "group": self._find_element(root, "groupId"),
            "artifact": self._find_element(root, "artifactId"),
            "version": self._find_element(root, "version"),
            "properties": self._parse_properties(root),
            "dependencies": self._parse_dependencies(root),
            "repositories": self._parse_repositories(root),
            "plugins": self._parse_plugins(root),
            "parent": self._parse_parent(root),
            "packaging": self._find_element(root, "packaging") or "jar",
            "modules": self.modules,
        }

        return project_info

    def _find_element(self, root, tag: str) -> str:
        element = root.find(tag)
        return element.text if element is not None else ""

    def _parse_properties(self, root) -> Dict:
        properties = {}
        props_elem = root.find("properties")
        if props_elem is not None:
            for prop in props_elem:
                properties[prop.tag] = prop.text
        return properties

    def _parse_dependencies(self, root) -> List[Dict]:
        dependencies = []
        deps_elem = root.find("dependencies")
        if deps_elem is not None:
            for dep in deps_elem.findall("dependency"):
                dependency = {
                    "group": self._find_element(dep, "groupId"),
                    "artifact": self._find_element(dep, "artifactId"),
                    "version": self._find_element(dep, "version"),
                    "scope": self._find_element(dep, "scope"),
                    "optional": self._find_element(dep, "optional"),
                }
                dependencies.append(dependency)
        return dependencies

    def _parse_repositories(self, root) -> List[Dict]:
        repositories = []
        repos_elem = root.find("repositories")
        if repos_elem is not None:
            for repo in repos_elem.findall("repository"):
                repository = {
                    "id": self._find_element(repo, "id"),
                    "url": self._find_element(repo, "url"),
                }
                repositories.append(repository)
        return repositories

    def _parse_plugins(self, root) -> List[Dict]:
        plugins = []
        build_elem = root.find("build")
        if build_elem is not None:
            # Parse plugin management section
            plugin_mgt = build_elem.find("pluginManagement/plugins")
            if plugin_mgt is not None:
                for plugin in plugin_mgt.findall("plugin"):
                    plugin_info = self._extract_plugin_info(plugin)
                    plugins.append(plugin_info)

            # Parse direct plugins section
            plugins_elem = build_elem.find("plugins")
            if plugins_elem is not None:
                for plugin in plugins_elem.findall("plugin"):
                    plugin_info = self._extract_plugin_info(plugin)
                    plugins.append(plugin_info)
        return plugins

    def _extract_plugin_info(self, plugin) -> Dict:
        config = plugin.find("configuration")
        executions = plugin.find("executions")

        return {
            "group": self._find_element(plugin, "groupId"),
            "artifact": self._find_element(plugin, "artifactId"),
            "version": self._find_element(plugin, "version"),
            "configuration": (
                self._parse_configuration(config) if config is not None else {}
            ),
            "executions": (
                self._parse_executions(executions) if executions is not None else []
            ),
        }

    def _parse_configuration(self, config) -> Dict:
        result = {}
        for child in config:
            result[child.tag] = child.text
        return result

    def _parse_executions(self, executions) -> List[Dict]:
        result = []
        for execution in executions.findall("execution"):
            exec_info = {
                "id": self._find_element(execution, "id"),
                "phase": self._find_element(execution, "phase"),
                "goals": [goal.text for goal in execution.findall("goals/goal")],
            }
            result.append(exec_info)
        return result

    def generate_build_gradle(self, project_info: Dict):
        plugins_block = self._generate_plugins(project_info)
        build_gradle = f"""plugins {{
            {plugins_block}
        }}

        group = '{project_info["group"]}'
        version = '{project_info["version"]}'
        sourceCompatibility = '{project_info["properties"].get("java.version", "17")}'

        configurations {{
            compileOnly {{
                extendsFrom annotationProcessor
            }}
        }}

        repositories {{
            mavenCentral()
        {self._generate_repositories(project_info)}
        }}

        dependencies {{
        {self._generate_dependencies(project_info)}
        }}

        bootJar {{
            archiveFileName = "{project_info['artifact']}.jar"
            manifest {{
                attributes 'Start-Class': '{project_info["group"]}.{project_info["artifact"]}.Application'
            }}
        }}

        tasks.named('test') {{
            useJUnitPlatform()
            systemProperty 'file.encoding', 'UTF-8'
        }}

        tasks.named('compileJava') {{
            options.encoding = 'UTF-8'
        }}

        tasks.named('javadoc') {{
            options.encoding = 'UTF-8'
        }}
        """
        with open(os.path.join(self.project_path, "build.gradle"), "w") as f:
            f.write(build_gradle)

    def _generate_plugins(self, project_info: Dict) -> str:
        """Generate Gradle plugins dynamically from POM"""
        # Essential plugins that Gradle needs
        plugins: Dict[str, Optional[str]] = {
            "java": None  # Core Java plugin is always needed
        }

        # Add Spring Boot and dependency management plugins if Spring Boot is used
        if any(
            dep["group"].startswith("org.springframework.boot")
            for dep in project_info["dependencies"]
        ):
            spring_boot_version = self._get_spring_boot_version(project_info)
            plugins["org.springframework.boot"] = spring_boot_version
            plugins["io.spring.dependency-management"] = "1.1.4"

        # Generate plugin block
        plugin_block = ""
        for plugin_id, version in plugins.items():
            if version:
                plugin_block += f"    id '{plugin_id}' version '{version}'\n"
            else:
                plugin_block += f"    id '{plugin_id}'\n"

        return plugin_block

    def _convert_to_gradle_plugin_id(self, plugin: Dict) -> Optional[str]:
        """Convert Maven plugin coordinates to Gradle plugin ID."""
        group_id = plugin["group"]
        artifact_id = plugin["artifact"]

        # Skip Maven-specific plugins
        if "maven-plugin" in artifact_id and group_id == "org.apache.maven.plugins":
            return None

        # Remove common suffixes
        for suffix in ["-maven-plugin", "-plugin"]:
            if artifact_id.endswith(suffix):
                artifact_id = artifact_id[: -len(suffix)]

        # Handle special cases
        if group_id == "org.springframework.boot":
            return "org.springframework.boot"
        elif group_id == "org.projectlombok":
            return "io.freefair.lombok"
        elif group_id == "com.google.cloud.tools":
            return f"{group_id}.{artifact_id}"

        # For other plugins, create Gradle plugin ID from group and artifact
        # Convert Maven coordinates to Gradle plugin ID format
        plugin_id = f"{group_id}.{artifact_id}"
        plugin_id = plugin_id.replace("-", ".")

        return plugin_id

    def _generate_repositories(self, project_info: Dict) -> str:
        repo_block = ""
        for repo in project_info["repositories"]:
            repo_block += f"    maven {{ url '{repo['url']}' }}\n"
        return repo_block

    def _generate_dependencies(self, project_info: Dict) -> str:
        dep_block = ""
        for dep in project_info["dependencies"]:
            config = "implementation"
            if dep["scope"] == "test":
                config = "testImplementation"
            elif dep["scope"] == "runtime":
                config = "runtimeOnly"

            if dep["optional"] == "true":
                config = "compileOnly"

            dep_block += f"    {config} '{dep['group']}:{dep['artifact']}'\n"
        return dep_block

    def _get_spring_boot_version(self, project_info: Dict) -> str:
        for dep in project_info["dependencies"]:
            if (
                dep["group"] == "org.springframework.boot"
                and dep["artifact"] == "spring-boot-starter-parent"
            ):
                return dep["version"]
        return "3.2.1"  # default version

    def generate_settings_gradle(self, project_info: Dict):
        """Generate settings.gradle with module includes"""
        settings_content = [f"rootProject.name = '{project_info['artifact']}'"]

        # Add module includes
        for module in project_info.get("modules", []):
            module_path = module.replace("/", ":")
            settings_content.append(f"include '{module_path}'")

        with open(os.path.join(self.project_path, "settings.gradle"), "w") as f:
            f.write("\n".join(settings_content))

    def generate_root_build_gradle(self, project_info: Dict):
        """Generate the root build.gradle with common configurations"""
        plugins_block = self._generate_plugins(project_info)
        build_gradle = f"""plugins {{
    {plugins_block}
}}

allprojects {{
    group = '{project_info["group"]}'
    version = '{project_info["version"]}'
    
    repositories {{
        mavenCentral()
{self._generate_repositories(project_info)}    }}
}}

subprojects {{
    apply plugin: 'java'
    apply plugin: 'io.spring.dependency-management'
    
    sourceCompatibility = '{project_info["properties"].get("java.version", "17")}'

    dependencies {{
        // Common dependencies for all modules
{self._generate_dependencies(project_info)}    }}
    
    test {{
        useJUnitPlatform()
    }}
}}"""
        with open(os.path.join(self.project_path, "build.gradle"), "w") as f:
            f.write(build_gradle)

    def generate_module_build_gradle(self, module_path: str, module_info: Dict):
        """Generate build.gradle for a specific module"""
        module_specific_plugins = self._generate_plugins(module_info)

        build_gradle = f"""plugins {{
    {module_specific_plugins}
}}

dependencies {{
{self._generate_dependencies(module_info)}}}

// Module specific configurations
{self._generate_module_specific_config(module_info)}
"""
        module_build_file = os.path.join(self.project_path, module_path, "build.gradle")
        os.makedirs(os.path.dirname(module_build_file), exist_ok=True)
        with open(module_build_file, "w") as f:
            f.write(build_gradle)

    def _generate_module_specific_config(self, module_info: Dict) -> str:
        """Generate module-specific configurations"""
        if module_info.get("packaging") == "war":
            return "apply plugin: 'war'"
        return ""

    def cleanup_maven_files(self):
        files_to_remove = ["pom.xml", "mvnw", "mvnw.cmd"]
        for file in files_to_remove:
            file_path = os.path.join(self.project_path, file)
            if os.path.exists(file_path):
                os.remove(file_path)

        mvn_dir = os.path.join(self.project_path, ".mvn")
        if os.path.exists(mvn_dir):
            shutil.rmtree(mvn_dir)

    def generate_gradle_wrapper(self):
        """Generate Gradle wrapper files"""
        try:
            subprocess.run(["gradle", "wrapper"], cwd=self.project_path, check=True)
        except Exception as e:
            print(f"Warning: Could not generate Gradle wrapper: {str(e)}")

    def convert(self):
        try:
            # Parse parent pom.xml
            project_info = self.parse_pom()

            if project_info["modules"]:
                # This is a multi-module project
                self.generate_settings_gradle(project_info)
                self.generate_root_build_gradle(project_info)

                # Convert each module
                for module in project_info["modules"]:
                    module_pom = os.path.join(self.project_path, module, "pom.xml")
                    if os.path.exists(module_pom):
                        module_converter = MavenToGradleConverter(
                            os.path.join(self.project_path, module)
                        )
                        module_info = module_converter.parse_pom()
                        self.generate_module_build_gradle(module, module_info)
            else:
                # Single module project
                self.generate_build_gradle(project_info)
                self.generate_settings_gradle(project_info)

            self.generate_gradle_wrapper()
            # self.cleanup_maven_files()

            print("Successfully converted Maven project to Gradle!")
            print("\nNext steps:")
            print("1. Review the generated build.gradle files")
            print("2. Run './gradlew clean build' to test the build")
            print("3. Run './gradlew bootRun' to start the application")
        except Exception as e:
            print(f"Error converting project: {str(e)}")


# Usage example
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python maven_to_gradle_converter.py <project_path>")
        sys.exit(1)

    converter = MavenToGradleConverter(sys.argv[1])
    converter.convert()
