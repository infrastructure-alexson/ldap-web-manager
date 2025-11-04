# Project Board Organization Guide

**Feature Tracking Project**: https://github.com/orgs/infrastructure-alexson/projects/1  
**Bug Tracking Project**: https://github.com/orgs/infrastructure-alexson/projects/2  
**Repository**: infrastructure-alexson/ldap-web-manager  
**Last Updated**: 2025-11-03

---

## Overview

This guide provides instructions for organizing the LDAP Web Manager project boards.

### Project Separation

- **Project #1** - Feature enhancements, roadmap items, new functionality (44 issues spanning v2.1.0 - v3.1.0)
- **Project #2** - Bug fixes, defects, issues with existing functionality

**Important**: All new bugs should be tracked on Project #2, not Project #1.

---

## Issue Organization by Version

### v2.1.0 - UI Completion & User Experience (16 issues)
**Timeline**: Nov 15 - Dec 15, 2025 (30 days)  
**Priority**: Most are normal, 4 high-priority IPAM features

| Issue # | Title | Priority |
|---------|-------|----------|
| #1 | [v2.1.0] IPAM Visual Interface - Subnet Calculator | Normal |
| #2 | [v2.1.0] IPAM Visual Interface - IP Search & Discovery | Normal |
| #3 | [v2.1.0] IPAM Visual Interface - Pool Management UI | Normal |
| #43 | [v2.1.0] IPAM Visual Interface - IP Allocation Map | High |
| #5 | [v2.1.0] Audit Log Viewer | Normal |
| #6 | [v2.1.0] Bulk User Operations | Normal |
| #7 | [v2.1.0] Bulk DNS Operations | Normal |
| #8 | [v2.1.0] Bulk IP Allocation | Normal |
| #9 | [v2.1.0] Enhanced UI - User Profile Page | Normal |
| #10 | [v2.1.0] Enhanced UI - Group Details Page | Normal |
| #11 | [v2.1.0] Enhanced UI - DNS Zone Editor | Normal |
| #12 | [v2.1.0] Enhanced UI - DHCP Subnet Wizard | Normal |
| #13 | [v2.1.0] Enhanced UI - Dashboard Widgets | Normal |
| #14 | [v2.1.0] Enhanced UI - Dark Mode | Normal |
| #42 | [v2.1.0] Service Account Management | Normal |
| #15 | [v2.1.0] Documentation Updates | Normal |

---

### v2.2.0 - IPv6 & Monitoring (10 issues)
**Timeline**: Jan 1 - Feb 15, 2026 (45 days)  
**Priority**: All normal

| Issue # | Title | Priority |
|---------|-------|----------|
| #16 | [v2.2.0] IPv6 Support - IPAM | Normal |
| #17 | [v2.2.0] IPv6 Support - DNS | Normal |
| #18 | [v2.2.0] IPv6 Support - DHCP | Normal |
| #19 | [v2.2.0] DHCP Lease Monitoring | Normal |
| #20 | [v2.2.0] LDAP Server Health Monitoring | Normal |
| #21 | [v2.2.0] Service Status Dashboard | Normal |
| #22 | [v2.2.0] Alerts & Notifications | Normal |
| #23 | [v2.2.0] Performance Enhancements - Caching | Normal |
| #24 | [v2.2.0] Performance Enhancements - Database Optimization | Normal |
| #25 | [v2.2.0] Performance Enhancements - Frontend | Normal |

---

### v2.3.0 - Automation & Workflows (4 issues)
**Timeline**: Mar 1 - Apr 15, 2026 (45 days)  
**Priority**: All normal

| Issue # | Title | Priority |
|---------|-------|----------|
| #26 | [v2.3.0] Workflow Engine | Normal |
| #27 | [v2.3.0] Template System | Normal |
| #28 | [v2.3.0] Scheduled Tasks | Normal |
| #29 | [v2.3.0] Advanced Reporting | Normal |

---

### v3.0.0 - Enterprise Features (6 issues)
**Timeline**: May 1 - Jun 30, 2026 (60 days)  
**Priority**: All normal

| Issue # | Title | Priority |
|---------|-------|----------|
| #30 | [v3.0.0] Multi-Tenancy Support | Normal |
| #31 | [v3.0.0] Delegated Administration | Normal |
| #32 | [v3.0.0] High Availability Setup | Normal |
| #33 | [v3.0.0] Advanced RBAC | Normal |
| #34 | [v3.0.0] Single Sign-On (SSO) | Normal |
| #35 | [v3.0.0] Enterprise Security Enhancements | Normal |

---

### v3.1.0 - API & Integrations (7 issues)
**Timeline**: Jul 15 - Aug 30, 2026 (45 days)  
**Priority**: All normal

| Issue # | Title | Priority |
|---------|-------|----------|
| #36 | [v3.1.0] GraphQL API | Normal |
| #37 | [v3.1.0] Webhooks | Normal |
| #38 | [v3.1.0] Batch Operations API | Normal |
| #39 | [v3.1.0] Ansible Module | Normal |
| #40 | [v3.1.0] Terraform Provider | Normal |
| #41 | [v3.1.0] Prometheus Metrics | Normal |
| #42 | [v3.1.0] Cloud DNS Integration (AWS, Azure, GCP, Cloudflare) | Normal |

---

## Step-by-Step Setup Instructions

### Step 1: Access the Project Board

1. Navigate to: https://github.com/orgs/infrastructure-alexson/projects/1
2. Ensure you have admin access to the organization project

### Step 2: Configure Project Settings

**A. Set Up Custom Fields**

Go to Settings → Fields and create:

1. **Version** (Single Select)
   - Options: `v2.1.0`, `v2.2.0`, `v2.3.0`, `v3.0.0`, `v3.1.0`
   - Default: None

2. **Priority** (Single Select)
   - Options: `High`, `Medium`, `Low`
   - Default: `Medium`

3. **Status** (Single Select - may already exist)
   - Options: `Todo`, `In Progress`, `Done`
   - Default: `Todo`

4. **Estimated Effort** (Number)
   - Unit: Days
   - Default: None

**B. Set Up Iterations**

Go to Settings → Iterations and create:

1. **v2.1.0**
   - Start: 2025-11-15
   - End: 2025-12-15
   - Duration: 30 days

2. **v2.2.0**
   - Start: 2026-01-01
   - End: 2026-02-15
   - Duration: 45 days

3. **v2.3.0**
   - Start: 2026-03-01
   - End: 2026-04-15
   - Duration: 45 days

4. **v3.0.0**
   - Start: 2026-05-01
   - End: 2026-06-30
   - Duration: 60 days

5. **v3.1.0**
   - Start: 2026-07-15
   - End: 2026-08-30
   - Duration: 45 days

### Step 3: Bulk Assign Issues to Iterations

**Method 1: Using Filters (Recommended)**

1. Click "Filter" in the project board
2. Enter filter: `label:v2.1.0`
3. Select all visible issues (Shift+Click or Ctrl+A)
4. Click the "..." menu → "Set iteration" → Select "v2.1.0"
5. Repeat for each version:
   - `label:v2.2.0` → Assign to v2.2.0 iteration
   - `label:v2.3.0` → Assign to v2.3.0 iteration
   - `label:v3.0.0` → Assign to v3.0.0 iteration
   - `label:v3.1.0` → Assign to v3.1.0 iteration

**Method 2: Manual Assignment**

For each issue in the project:
1. Click on the issue card
2. Set the "Iteration" field based on the version in the title
3. Set the "Version" field to match
4. Set "Priority" (High for issues #1-4, Medium for others)

### Step 4: Set Priority for High-Priority Issues

Filter by: `label:v2.1.0 label:high-priority`

Set Priority to "High" for issues:
- #1: IPAM Visual Interface - IP Allocation Map
- #2: IPAM Visual Interface - Subnet Calculator
- #3: IPAM Visual Interface - IP Search & Discovery
- #4: IPAM Visual Interface - Pool Management UI

### Step 5: Configure Board Views

**View 1: By Iteration (Default)**

1. Click "View" → "New View" → "Board"
2. Name: "By Iteration"
3. Group by: `Iteration`
4. Sort by: `Issue number` (ascending)
5. Show: All items

**View 2: By Priority**

1. Click "View" → "New View" → "Board"
2. Name: "By Priority"
3. Group by: `Priority`
4. Sort by: `Iteration` (ascending), then `Issue number` (ascending)
5. Show: All items

**View 3: Current Sprint (v2.1.0)**

1. Click "View" → "New View" → "Table"
2. Name: "v2.1.0 Sprint"
3. Filter: `iteration:v2.1.0`
4. Sort by: `Priority` (descending), then `Issue number` (ascending)
5. Columns: Issue, Status, Priority, Assignees, Labels

**View 4: Roadmap**

1. Click "View" → "New View" → "Roadmap"
2. Name: "Release Roadmap"
3. Group by: `Iteration`
4. Date field: `Iteration`
5. Show: All items

### Step 6: Sort and Order Issues

**Within Each Iteration Column**:

1. High-priority issues first (#1-4 in v2.1.0)
2. Then by logical grouping:
   - IPAM features together
   - Audit/Operations features together
   - UI enhancements together
   - Documentation last
3. Finally by issue number (ascending)

**Recommended Order for v2.1.0**:
1. #43 (IPAM IP Allocation Map - High)
2. #1 (IPAM Subnet Calculator)
3. #2 (IPAM IP Search)
4. #3 (IPAM Pool Management)
5. #5 (Audit Log)
6. #6 (Bulk Users)
7. #7 (Bulk DNS)
8. #8 (Bulk IP)
9. #42 (Service Accounts)
10. #9 (User Profile)
11. #10 (Group Details)
12. #11 (DNS Editor)
13. #12 (DHCP Wizard)
14. #13 (Dashboard Widgets)
15. #14 (Dark Mode)
16. #15 (Documentation)

---

## Verification Checklist

After setup, verify:

- [ ] All 43 issues are in the project
- [ ] Each issue has the correct "Iteration" assigned
- [ ] Each issue has the correct "Version" field
- [ ] Issues #1-4 have "High" priority
- [ ] All other issues have appropriate priority
- [ ] Iterations have correct start/end dates
- [ ] Board views are configured (By Iteration, By Priority, Current Sprint, Roadmap)
- [ ] Issues are sorted logically within each iteration
- [ ] Filters work correctly (test with `label:v2.1.0`, `priority:High`, etc.)

---

## Quick Reference: Filter Examples

### By Version
```
label:v2.1.0
label:v2.2.0
label:v2.3.0
label:v3.0.0
label:v3.1.0
```

### By Category
```
label:frontend
label:backend
label:security
label:performance
label:integration
label:high-priority
```

### Combined Filters
```
label:v2.1.0 label:frontend
label:v2.1.0 label:high-priority
label:backend label:security
iteration:v2.1.0 status:Todo
```

### By Assignee
```
assignee:@me
no:assignee
```

---

## Tips for Project Management

### For Sprint Planning

1. Use the "v2.1.0 Sprint" view for active development
2. Move issues from "Todo" → "In Progress" → "Done"
3. Assign team members to issues
4. Track progress daily

### For Release Planning

1. Use the "Release Roadmap" view to see timeline
2. Monitor iteration capacity (don't overcommit)
3. Adjust priorities based on dependencies
4. Review and update weekly

### For Stakeholder Communication

1. Use the "By Iteration" view for release overview
2. Filter by `label:high-priority` for critical features
3. Export to CSV for reporting (... menu → Export)
4. Share public project link with read-only access

---

## Automation Ideas (Future)

Consider setting up GitHub Actions workflows for:

1. **Auto-label**: Automatically apply version labels based on milestone
2. **Auto-assign**: Assign issues to iterations when created
3. **Status sync**: Update issue status when PR is merged
4. **Notifications**: Slack/email when iteration starts/ends
5. **Burndown**: Generate burndown charts for sprints

---

## Bug Tracking (Project #2)

### Creating Bug Reports

All bugs should be created with the `bug` label and added to **Project #2** instead of Project #1.

**Command to create a bug**:
```bash
gh issue create --repo infrastructure-alexson/ldap-web-manager \
  --title "[BUG] Brief description" \
  --label bug \
  --body "Description of the bug..."
```

**Add to Bug Tracking Project**:
```bash
gh project item-add 2 --owner infrastructure-alexson \
  --url https://github.com/infrastructure-alexson/ldap-web-manager/issues/<number>
```

### Bug Severity Levels

Use additional labels to indicate severity:
- `severity:critical` - System down, data loss, security vulnerability
- `severity:high` - Major functionality broken, blocking users
- `severity:medium` - Feature partially working, workaround available
- `severity:low` - Minor issue, cosmetic, edge case

### Bug Workflow

1. **Report**: Create issue with `bug` label
2. **Triage**: Assign severity and priority
3. **Add to Project #2**: Ensure it's on the bug tracking board
4. **Assign**: Assign to developer
5. **Fix**: Create branch, fix, test, PR
6. **Verify**: QA verification
7. **Close**: Close issue when fix is deployed

### Bug vs Feature

**It's a bug if**:
- Existing functionality doesn't work as documented
- Error messages or crashes occur
- Data corruption or loss
- Security vulnerability
- Performance regression

**It's a feature if**:
- Requesting new functionality
- Enhancement to existing feature
- Change in behavior (not broken)
- Documentation improvement

When in doubt, start with `bug` label and let triage reassign if needed.

---

## Troubleshooting

### Issue not showing in project
- Verify it's added: `gh project item-add 1 --owner infrastructure-alexson --url <issue-url>`
- Check if filters are hiding it

### Can't assign to iteration
- Ensure iterations are created in project settings
- Check that issue is in the project first

### Wrong version label
- Update with: `gh issue edit <number> --repo infrastructure-alexson/ldap-web-manager --add-label v2.1.0 --remove-label v2.2.0`

### Bulk operations not working
- Try using smaller batches (10-15 issues at a time)
- Use keyboard shortcuts (Shift+Click to select range)
- Refresh page if UI becomes unresponsive

---

## Resources

### Project Boards
- **Feature Tracking (Project #1)**: https://github.com/orgs/infrastructure-alexson/projects/1
- **Bug Tracking (Project #2)**: https://github.com/orgs/infrastructure-alexson/projects/2

### Repository & Issues
- **Repository**: https://github.com/infrastructure-alexson/ldap-web-manager
- **All Issues**: https://github.com/infrastructure-alexson/ldap-web-manager/issues
- **Features Only**: https://github.com/infrastructure-alexson/ldap-web-manager/issues?q=is%3Aissue+is%3Aopen+-label%3Abug
- **Bugs Only**: https://github.com/infrastructure-alexson/ldap-web-manager/issues?q=is%3Aissue+is%3Aopen+label%3Abug

### Documentation
- **Roadmap**: [doc/ROADMAP.md](ROADMAP.md)
- **Issue Summary**: [doc/ISSUE-CREATION-SUMMARY.md](ISSUE-CREATION-SUMMARY.md)

---

**Last Updated**: 2025-11-03  
**Total Issues**: 44  
**Versions**: 5 (v2.1.0 - v3.1.0)  
**Planning Horizon**: 9 months (Nov 2025 - Aug 2026)

