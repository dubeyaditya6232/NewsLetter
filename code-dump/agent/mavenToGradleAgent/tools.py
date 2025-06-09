from google import genai
import os
import json


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
        # Ensure a dict is always returned
        return {"error": "Unknown error occurred in _run method"}
