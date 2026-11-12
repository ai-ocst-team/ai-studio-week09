"""Record reproducible, quoted shell commands and their actual outputs."""
from pathlib import Path
import shlex
import subprocess


def record(path, commands):
    sections = []
    for arguments in commands:
        command = shlex.join(arguments)
        result = subprocess.run(["zsh", "-f", "-c", command], text=True, capture_output=True)
        if result.returncode != 0:
            raise SystemExit(f"Audit command failed: {command}\n{result.stderr}")
        sections.append(
            f"$ {command}\n{result.stdout or '(no stdout)' }\n"
            f"stderr: {result.stderr or '(empty)'}\nexit={result.returncode}\n"
        )
    Path(path).write_text("\n".join(sections))


record("evidence/task5/env_audit.txt", [
    ["git", "rev-parse", "HEAD", "main", "origin/main"],
    ["git", "rev-parse", "--is-shallow-repository"],
    ["git", "log", "--all", "--full-history", "--format=%h %s", "--", "**/.env*", ".env*"],
    ["git", "log", "--all", "--full-history", "--format=%h %s", "--", "**.env*"],
    ["git", "check-ignore", ".env", "nested/.env", ".env.production"],
    [".venv/bin/python", "-c", "import subprocess; from pathlib import Path; paths = subprocess.check_output(['git', 'ls-files', '--cached', '-z']).decode().split('\\0'); print('\\n'.join(p for p in paths if Path(p).name.startswith('.env')) or '(no matching paths)')"],
])
record("evidence/task5/source_scan.txt", [
    ["rg", "-n", r"print\(|logging|requests|http|api_key|API_KEY|password|secret|token|subprocess|eval\(|exec\(",
     "--glob", "*.py", "prepare_photo", "analyze_with_gemini", "validate_vlm_response",
     "clean_analysis_dataframe", "aggregate_photo_insights", "scripts"],
])
print("Audit commands executed in zsh; quoted commands, stdout, stderr and exit codes recorded.")
