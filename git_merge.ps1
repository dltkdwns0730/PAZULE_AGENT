Set-Location "C:\Users\irubw\geminiProject\projects\active\PAZULE"

$NEW_BRANCH = "perf/pipeline-concurrency-api-stability"
$OLD_BRANCH = "fix/routing-and-style-issues"

# ── Step 1: 현재 main 위 변경사항 커밋 ─────────────────────────────────────
Write-Host "[1/7] Committing working-tree changes on main..." -ForegroundColor Cyan
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  (nothing to commit, skipping)" -ForegroundColor DarkGray
} else {
    git commit -F .git/COMMIT_MSG_TEMP
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: commit" -ForegroundColor Red; exit 1 }
    Write-Host "OK" -ForegroundColor Green
}

# ── Step 2: fix 브랜치로 전환 후 새 이름으로 rename ───────────────────────
Write-Host "[2/7] Renaming $OLD_BRANCH -> $NEW_BRANCH..." -ForegroundColor Cyan
git checkout $OLD_BRANCH
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: checkout $OLD_BRANCH" -ForegroundColor Red; exit 1 }
git branch -m $NEW_BRANCH
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: rename branch" -ForegroundColor Red; exit 1 }
git checkout main
Write-Host "OK" -ForegroundColor Green

# ── Step 3: 새 이름으로 origin push ────────────────────────────────────────
Write-Host "[3/7] Pushing $NEW_BRANCH to origin..." -ForegroundColor Cyan
git push origin $NEW_BRANCH
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: push $NEW_BRANCH" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

# ── Step 4: 구 브랜치 origin에서 삭제 ─────────────────────────────────────
Write-Host "[4/7] Deleting $OLD_BRANCH from origin..." -ForegroundColor Cyan
git push origin --delete $OLD_BRANCH
Write-Host "OK" -ForegroundColor Green

# ── Step 5: main 최신화 ────────────────────────────────────────────────────
Write-Host "[5/7] Pulling origin/main..." -ForegroundColor Cyan
git stash
git pull origin main --no-rebase
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: pull" -ForegroundColor Red; exit 1 }
git stash pop
Write-Host "OK" -ForegroundColor Green

# ── Step 6: merge ──────────────────────────────────────────────────────────
Write-Host "[6/7] Merging $NEW_BRANCH into main..." -ForegroundColor Cyan
git merge $NEW_BRANCH --no-ff -m "merge: integrate pipeline concurrency and API stability improvements"
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: merge - resolve conflicts manually" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

# ── Step 7: main push ──────────────────────────────────────────────────────
Write-Host "[7/7] Pushing main to origin..." -ForegroundColor Cyan
git push origin main
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: push main" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

Write-Host ""
Write-Host "All done!" -ForegroundColor Green
git log --oneline -5
