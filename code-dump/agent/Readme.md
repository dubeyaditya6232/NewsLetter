# Maven to Gradle AI Migration Agent

This project provides an automated AI-powered agent to migrate Java Maven projects to Gradle. It leverages Google Gemini LLM to convert Maven `pom.xml` files into Gradle build files, iteratively fixes build issues, and ensures a successful Gradle build.
(Note: support only single module application)

## Features
- Converts Maven projects to Gradle using LLM (Google Gemini).
- Writes and fixes `build.gradle` and `settings.gradle` files as needed.
- Automatically generates the Gradle wrapper.
- Runs `gradle clean build` and attempts to fix build errors up to 5 times using the LLM.
- Backs up and removes Maven files after a successful migration.
- Modular, maintainable, and extensible codebase.

## Project Structure
```
.
├── main.py                     # Main agent runner
├── mavenToGradleAgent/
│   ├── gradle_build.py         # Gradle build and wrapper logic
│   ├── tools.py                # LLM Gradle converter tool
│   ├── utils.py                # Utility functions
│   └── ...
├── springbootApplication/      # Example Java project (post-migration)
│   ├── build.gradle
│   ├── gradlew, gradlew.bat
│   └── ...
└── README.md
```

## Requirements
- Python 3.8+
- Google Gemini API key (set as `GOOGLE_API_KEY` environment variable)
- Java and Gradle installed on your system

## Installation
1. Clone this repository.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set your Google Gemini API key:
   ```sh
   set GOOGLE_API_KEY=your_api_key_here  # Windows
   # or
   export GOOGLE_API_KEY=your_api_key_here  # Linux/macOS
   ```

## Usage
1. Place your Maven project in a directory (e.g., `./path_to_maven_project`).
2. Run the migration agent:
   ```sh
   python main.py ./path_to_maven_project
   ```
   Or set the environment variable `MAVEN_PROJECT_DIR` and run without arguments.

3. The agent will:
   - Use the LLM to generate Gradle files from `pom.xml`.
   - Write and fix Gradle files as needed.
   - Generate the Gradle wrapper.
   - Run and fix `gradle clean build` up to 5 times if needed.
   - Backup and remove Maven files after a successful migration.

## Customization & Extensibility
- The agent logic is modular. You can extend or swap out the LLM tool, utility functions, or build logic as needed.
- See `mavenToGradleAgent/` for reusable modules.

## Troubleshooting
- Ensure your `GOOGLE_API_KEY` is set and valid.
- Make sure Java and Gradle are installed and available in your PATH.
- If migration fails after 5 attempts, manual intervention may be required. Check the logs for details.


## Acknowledgements
- Google Gemini for LLM-powered code generation.
- Open source Gradle and Maven communities.
