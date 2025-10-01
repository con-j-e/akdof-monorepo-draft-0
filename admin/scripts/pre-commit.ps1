$branch = git branch --show-current

if ($branch -eq "main") {
    Write-Host "Direct commits to main are not allowed." -ForegroundColor Red
    Write-Host "Please create a feature branch and submit a PR." -ForegroundColor Yellow
    exit 1
}

exit 0