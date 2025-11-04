# Organize GitHub Issues - Create Labels, Add to Project, Assign Iterations
$ErrorActionPreference = "Stop"
$repo = "infrastructure-alexson/ldap-web-manager"
$projectNumber = 1
$orgName = "infrastructure-alexson"

Write-Host "Organizing GitHub issues..." -ForegroundColor Cyan
Write-Host ""

# Change to the repository directory
Set-Location "C:\Users\Steven Alexson\Code\infrastructure\ldap-web-manager"

# Create version labels
Write-Host "Creating version labels..." -ForegroundColor Yellow

gh label create "v2.1.0" --repo $repo --description "Features planned for v2.1.0 release" --color "0366d6" --force
gh label create "v2.2.0" --repo $repo --description "Features planned for v2.2.0 release" --color "1d76db" --force
gh label create "v2.3.0" --repo $repo --description "Features planned for v2.3.0 release" --color "2ea44f" --force
gh label create "v3.0.0" --repo $repo --description "Features planned for v3.0.0 release" --color "fbca04" --force
gh label create "v3.1.0" --repo $repo --description "Features planned for v3.1.0 release" --color "d4c5f9" --force
gh label create "v3.2.0" --repo $repo --description "Features planned for v3.2.0+ release" --color "c5def5" --force

# Create other useful labels
gh label create "high-priority" --repo $repo --description "High priority feature" --color "d93f0b" --force
gh label create "backend" --repo $repo --description "Backend work required" --color "5319e7" --force
gh label create "frontend" --repo $repo --description "Frontend work required" --color "1d76db" --force
gh label create "security" --repo $repo --description "Security related" --color "d73a4a" --force
gh label create "performance" --repo $repo --description "Performance improvement" --color "0e8a16" --force
gh label create "integration" --repo $repo --description "Third-party integration" --color "fbca04" --force
gh label create "devops" --repo $repo --description "DevOps/deployment related" --color "bfdadc" --force
gh label create "monitoring" --repo $repo --description "Monitoring and observability" --color "c2e0c6" --force

Write-Host "Labels created successfully!" -ForegroundColor Green
Write-Host ""

# Now add the labels to the existing issues
Write-Host "Adding version labels to issues..." -ForegroundColor Yellow

# Get all open issues
$issues = gh issue list --repo $repo --limit 1000 --state open --json number,title | ConvertFrom-Json

foreach ($issue in $issues) {
    $issueNumber = $issue.number
    $title = $issue.title
    
    # Determine version label from title
    if ($title -like "*[v2.1.0]*") {
        gh issue edit $issueNumber --repo $repo --add-label "v2.1.0" 2>$null
        Write-Host "  Added v2.1.0 label to #$issueNumber" -ForegroundColor Gray
    }
    elseif ($title -like "*[v2.2.0]*") {
        gh issue edit $issueNumber --repo $repo --add-label "v2.2.0" 2>$null
        Write-Host "  Added v2.2.0 label to #$issueNumber" -ForegroundColor Gray
    }
    elseif ($title -like "*[v2.3.0]*") {
        gh issue edit $issueNumber --repo $repo --add-label "v2.3.0" 2>$null
        Write-Host "  Added v2.3.0 label to #$issueNumber" -ForegroundColor Gray
    }
    elseif ($title -like "*[v3.0.0]*") {
        gh issue edit $issueNumber --repo $repo --add-label "v3.0.0" 2>$null
        Write-Host "  Added v3.0.0 label to #$issueNumber" -ForegroundColor Gray
    }
    elseif ($title -like "*[v3.1.0]*") {
        gh issue edit $issueNumber --repo $repo --add-label "v3.1.0" 2>$null
        Write-Host "  Added v3.1.0 label to #$issueNumber" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Labels added successfully!" -ForegroundColor Green
Write-Host ""

# Add all issues to the project
Write-Host "Adding issues to project..." -ForegroundColor Yellow

foreach ($issue in $issues) {
    $issueNumber = $issue.number
    $issueUrl = "https://github.com/$repo/issues/$issueNumber"
    
    try {
        gh project item-add $projectNumber --owner $orgName --url $issueUrl 2>$null
        Write-Host "  Added issue #$issueNumber to project" -ForegroundColor Gray
    }
    catch {
        Write-Host "  Issue #$issueNumber may already be in project" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "All issues added to project!" -ForegroundColor Green
Write-Host ""

Write-Host "Organization complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  - Labels created and applied" -ForegroundColor White
Write-Host "  - All issues added to project" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Visit the project: https://github.com/orgs/$orgName/projects/$projectNumber" -ForegroundColor White
Write-Host "  2. Set up iterations in the project settings" -ForegroundColor White
Write-Host "  3. Assign issues to iterations:" -ForegroundColor White
Write-Host "     - v2.1.0: Nov 15 - Dec 15, 2025" -ForegroundColor White
Write-Host "     - v2.2.0: Jan 1 - Feb 15, 2026" -ForegroundColor White
Write-Host "     - v2.3.0: Mar 1 - Apr 15, 2026" -ForegroundColor White
Write-Host "     - v3.0.0: May 1 - Jun 30, 2026" -ForegroundColor White
Write-Host "     - v3.1.0: Jul 15 - Aug 30, 2026" -ForegroundColor White
Write-Host ""

