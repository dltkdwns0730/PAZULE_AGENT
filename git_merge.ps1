Set-Location "C:\Users\irubw\geminiProject\projects\active\PAZULE"

# ── Step 1: 현재 작업 상태 커밋 (main 위 최신 변경 사항) ──────────────────
Write-Host "[1/7] Committing latest working-tree changes on main..." -ForegroundColor Cyan
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  (nothing to commit, skipping)" -ForegroundColor DarkGray
} else {
    git commit -F .git/COMMIT_MSG_TEMP
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: commit" -ForegroundColor Red; exit 1 }
    Write-Host "OK" -ForegroundColor Green
}

# ── Step 2: 새 브랜치명으로 로컬 rename ────────────────────────────────────
Write-Host "[2/7] Renaming branch: fix/routing-and-style-issues -> feat/pipeline-concurrency-api-stability..." -ForegroundColor Cyan
git branch -m fix/routing-and-style-issues feat/pipeline-concurrency-api-stability 2>$null
if ($LASTEXITCODE -ne 0) {
    # 이미 main에 있는 경우 — checkout 후 rename
    git checkout fix/routing-and-style-issues
    git branch -m feat/pipeline-concurrency-api-stability
    git checkout main
}
Write-Host "OK" -ForegroundColor Green

# ── Step 3: 변경된 이름으로 origin에 push ──────────────────────────────────
Write-Host "[3/7] Pushing renamed branch to origin..." -ForegroundColor Cyan
git push origin feat/pipeline-concurrency-api-stability
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: push renamed branch" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

# ── Step 4: 구 브랜치 origin에서 삭제 ─────────────────────────────────────
Write-Host "[4/7] Deleting old branch from origin..." -ForegroundColor Cyan
git push origin --delete fix/routing-and-style-issues 2>$null
Write-Host "OK (or already deleted)" -ForegroundColor Green

# ── Step 5: main 최신화 ─────────────────────────────────────────────────────
Write-Host "[5/7] Pulling origin/main..." -ForegroundColor Cyan
git stash 2>$null
git pull origin main
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: pull origin/main" -ForegroundColor Red; exit 1 }
git stash pop 2>$null
Write-Host "OK" -ForegroundColor Green

# ── Step 6: merge ───────────────────────────────────────────────────────────
Write-Host "[6/7] Merging feat/pipeline-concurrency-api-stability into main..." -ForegroundColor Cyan
git merge feat/pipeline-concurrency-api-stability --no-ff -m "merge: integrate pipeline concurrency and API stability improvements"
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: merge - resolve conflicts manually" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

# ── Step 7: push main ──────────────────────────────────────────────────────
Write-Host "[7/7] Pushing main to origin..." -ForegroundColor Cyan
git push origin main
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: push main" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

Write-Host ""
Write-Host "All done!" -ForegroundColor Green
git log --oneline -5
