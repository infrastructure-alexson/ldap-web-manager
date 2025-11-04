# Fix Issue Labels - Remove incorrect version labels
$ErrorActionPreference = "Stop"
$repo = "infrastructure-alexson/ldap-web-manager"

Write-Host "Fixing issue labels..." -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Steven Alexson\Code\infrastructure\ldap-web-manager"

# Get all open issues
$issues = gh issue list --repo $repo --limit 100 --state open --json number,title,labels | ConvertFrom-Json

$versionLabels = @("v2.1.0", "v2.2.0", "v2.3.0", "v3.0.0", "v3.1.0", "v3.2.0")

foreach ($issue in $issues) {
    $issueNumber = $issue.number
    $title = $issue.title
    $currentLabels = $issue.labels | ForEach-Object { $_.name }
    
    # Determine correct version from title
    $correctVersion = $null
    if ($title -match '^\[v(\d+\.\d+\.\d+)\]') {
        $correctVersion = "v$($matches[1])"
    }
    
    if ($correctVersion) {
        # Check if issue has incorrect version labels
        $incorrectLabels = $currentLabels | Where-Object { $versionLabels -contains $_ -and $_ -ne $correctVersion }
        
        if ($incorrectLabels) {
            Write-Host "Issue #$issueNumber ($correctVersion):" -ForegroundColor Yellow
            foreach ($label in $incorrectLabels) {
                gh issue edit $issueNumber --repo $repo --remove-label $label 2>$null
                Write-Host "  Removed incorrect label: $label" -ForegroundColor Gray
            }
        }
        
        # Ensure correct label is present
        if ($correctVersion -notin $currentLabels) {
            gh issue edit $issueNumber --repo $repo --add-label $correctVersion 2>$null
            Write-Host "  Added correct label: $correctVersion" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "Label cleanup complete!" -ForegroundColor Green
Write-Host ""

# Display summary
Write-Host "Summary by version:" -ForegroundColor Cyan
foreach ($version in $versionLabels) {
    $count = ($issues | Where-Object { $_.title -like "*[$version]*" }).Count
    if ($count -gt 0) {
        Write-Host "  $version : $count issues" -ForegroundColor White
    }
}

