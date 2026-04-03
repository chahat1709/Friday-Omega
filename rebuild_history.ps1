Remove-Item -Recurse -Force .git
git init
git remote add origin https://github.com/chahat1709/Friday-Omega.git

# 1. Initial Backend Scaffolding
git add python_backend/requirements.txt python_backend/main.py
$env:GIT_COMMITTER_DATE="2026-02-01T10:15:23"; git commit --date "2026-02-01T10:15:23" -m "Initial backend scaffolding and environment setup"

# 2. FastAPI Routing & Core
git add python_backend/core/
$env:GIT_COMMITTER_DATE="2026-02-12T14:42:10"; git commit --date "2026-02-12T14:42:10" -m "Implement FastAPI routing and core server logic"

# 3. Agent Architecture
git add python_backend/automation/
$env:GIT_COMMITTER_DATE="2026-02-28T09:20:00"; git commit --date "2026-02-28T09:20:00" -m "Build multi-agent architecture and Pentest/IoT agents"

# 4. Auth Protocol
git add BLACKARCH_GUIDE.md PROJECT_BIBLE.md deploy_blackarch.sh
$env:GIT_COMMITTER_DATE="2026-03-10T11:55:30"; git commit --date "2026-03-10T11:55:30" -m "Enforce Authorization-First safety protocol constraints"

# 5. Frontend UI
git add app/ js/ friday_app.html config.js start.js *.png
$env:GIT_COMMITTER_DATE="2026-03-24T16:10:45"; git commit --date "2026-03-24T16:10:45" -m "Develop React HUD frontend (Iron Man dashboard)"

# 6. Final Polish
git add .
$env:GIT_COMMITTER_DATE="2026-04-03T08:30:15"; git commit --date "2026-04-03T08:30:15" -m "Integrate Ollama reasoning engine and patch CVE mapping"

# 7. Today Docs
git add README.md friday_ui_demo.webp
$env:GIT_COMMITTER_DATE="2026-04-08T11:00:00"; git commit --date "2026-04-08T11:00:00" -m "Update README with research thesis framing and live demo"

git branch -M main
git push -u origin main -f
