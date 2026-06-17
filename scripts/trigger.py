import subprocess, json
# Get token
token = subprocess.run(["cat", "/tmp/gt.txt"], capture_output=True, text=True).stdout.strip()
# Build curl command
cmd = [
    "curl", "-s", "-x", "http://127.0.0.1:7897",
    "-X", "POST",
    "-H", f"Authorization: Bearer {token}",
    "-H", "Accept: application/vnd.github+json",
    "-d", '{"ref":"main"}',
    "-w", " HTTP %{http_code}",
    "https://api.github.com/repos/mdmodule/world-cup-2026-widget/actions/workflows/update-wc26.yml/dispatches"
]
result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
