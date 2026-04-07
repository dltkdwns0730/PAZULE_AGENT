Set-Location "C:\Users\irubw\geminiProject\projects\active\PAZULE"

Write-Host "[1/6] Stashing local changes on main..." -ForegroundColor Cyan
git stash
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: stash" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

Write-Host "[2/6] Pulling origin/main..." -ForegroundColor Cyan
git pull origin main
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: pull" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

Write-Host "[3/6] Restoring stashed changes..." -ForegroundColor Cyan
git stash pop
Write-Host "OK (conflicts if any shown above)" -ForegroundColor Green

Write-Host "[4/6] Committing current working tree changes on main..." -ForegroundColor Cyan
git add -A
git commit -m "chore: apply post-refactor adjustments (revert timeout, update model IDs, restructure LLM priority)"
if ($LASTEXITCODE -ne 0) { Write-Host "Nothing to commit or FAILED" -ForegroundColor Yellow }
Write-Host "OK" -ForegroundColor Green

Write-Host "[5/6] Merging fix/routing-and-style-issues into main..." -ForegroundColor Cyan
git merge fix/routing-and-style-issues --no-ff -m "merge: integrate pipeline concurrency and API stability improvements into main"
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: merge - resolve conflicts manually" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

Write-Host "[6/6] Pushing main to origin..." -ForegroundColor Cyan
git push origin main
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: push main" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

Write-Host "All done! Merge complete." -ForegroundColor Green
git log --oneline -5
