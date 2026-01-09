# Auto-Assign Issues Workflow

## Overview

The `auto-assign-issues.yml` workflow automatically manages issues and pull requests when you create a new branch with an issue number in its name. This streamlines the development workflow by:

1. Creating a draft pull request automatically
2. Linking the issue to the PR
3. Moving the issue to "In Progress" status in GitHub Projects
4. Auto-generating PR title and description

## How It Works

### Trigger

The workflow runs automatically when a new branch is created in the repository.

### Branch Naming Convention

To activate this workflow, include an issue number in your branch name using one of these patterns:

- `issue-123` - Simple issue prefix
- `123-feature-name` - Issue number at the start
- `feature/issue-123` - Issue number in path
- `fix/123-bug-description` - Number after prefix
- `issue_123` - Underscore separator

The workflow will extract the **first number** found in the branch name and use it as the issue number.

### Examples

```bash
# All of these will link to Issue #42:
git checkout -b issue-42
git checkout -b 42-add-login-feature
git checkout -b feature/issue-42
git checkout -b fix/42-security-patch
```

## What Gets Created

### 1. Draft Pull Request

A draft PR is automatically created with:

- **Title**: `[Issue #X] <Issue Title>`
- **Description**: Auto-generated with:
  - Link to the related issue
  - Issue description
  - Basic checklist template
- **Base Branch**: Automatically determined (typically `main` or `master`)
- **Status**: Draft (ready to be marked as ready for review when you're done)

### 2. Issue Link

The workflow:
- Links the PR to the issue using "Closes #X" in the PR description
- Adds a comment to the issue with a link to the new PR

### 3. Project Status Update

If the issue is part of a GitHub Project:
- Automatically moves the issue to "In Progress" status
- Works with GitHub Projects V2

## Workflow Steps

1. **Extract Issue Number**: Parses the branch name to find the issue number
2. **Determine Base Branch**: Identifies the main branch (main/master)
3. **Get Issue Details**: Fetches the issue title and description from GitHub
4. **Generate PR Content**: Creates title and description based on the issue
5. **Create Draft PR**: Opens a new draft pull request
6. **Link Issue**: Adds comment to issue and uses "Closes #X" syntax
7. **Update Project**: Moves issue to "In Progress" in all associated projects

## Requirements

### Permissions

The workflow requires these GitHub permissions:
- `contents: write` - To access repository content
- `pull-requests: write` - To create pull requests
- `issues: write` - To comment on issues
- Projects access - To update project status (configured in repository settings)

### Issue Must Exist

The workflow only creates a PR if:
- The issue number exists in the repository
- The issue is accessible (not deleted or private)

### No Duplicate PRs

If a PR already exists for the branch, the workflow will:
- Skip PR creation
- Still link to the existing PR in issue comments

## Customization

You can customize the workflow by editing `.github/workflows/auto-assign-issues.yml`:

### Base Branch Logic

Currently defaults to `main` or `master`. To use a different branch:

```yaml
# Modify the "Determine base branch" step
BASE_BRANCH="develop"  # or your preferred branch
```

### PR Template

The PR description template can be customized in the "Generate PR title and description" step:

```bash
PR_DESCRIPTION="## Related Issue
Closes #${ISSUE_NUM}

## Your Custom Sections Here
...
```

### Project Status Name

If your project uses a different status name than "In Progress":

```javascript
// Modify this line in the "Link issue to PR" step:
option => option.name === 'In Progress' || option.name === 'Your Status Name'
```

## Troubleshooting

### Workflow Doesn't Run

**Issue**: No PR is created when pushing a new branch

**Solutions**:
- Ensure branch name contains an issue number
- Check that the issue exists and is open
- Verify GitHub Actions are enabled in repository settings
- Check workflow run logs in Actions tab

### "Issue Not Found" Error

**Issue**: Workflow runs but fails to find the issue

**Solutions**:
- Verify the issue number exists in this repository
- Ensure issue is not deleted or in a different repository
- Check that the number is extracted correctly (see workflow logs)

### PR Already Exists

**Issue**: Workflow says PR already exists

**Explanation**: This is expected behavior. If you:
- Delete and recreate a branch
- Push to an existing branch

The workflow will skip duplicate PR creation.

### Project Status Not Updated

**Issue**: PR is created but project status doesn't change

**Solutions**:
- Verify the issue is added to a GitHub Project
- Check that the project has a "Status" field
- Ensure the status field has an "In Progress" option
- Verify repository has project write permissions

## Best Practices

1. **Always include issue number**: Make it a habit to include issue numbers in branch names
2. **Use consistent naming**: Pick a pattern (e.g., `issue-X`) and stick with it
3. **Check the draft PR**: Review auto-generated content before marking as ready
4. **Update description**: Add specific details about your changes
5. **Mark ready when done**: Convert from draft to ready for review when complete

## Integration with Development Workflow

### Recommended Workflow

1. **Find or create an issue** describing what you'll work on
2. **Create a branch** with the issue number in the name:
   ```bash
   git checkout -b issue-123
   ```
3. **Push the branch** to trigger the workflow:
   ```bash
   git push -u origin issue-123
   ```
4. **Check GitHub**: A draft PR should now exist, linked to the issue
5. **Make your changes** and commit normally
6. **Update PR description** with specific implementation details
7. **Mark PR as ready** when you're done and want review

### Benefits

- **Saves time**: No manual PR creation
- **Consistent format**: All PRs follow the same template
- **Better tracking**: Issues automatically linked to PRs
- **Project visibility**: Stakeholders see progress in project boards
- **Less context switching**: Stay in your terminal/IDE

## Summary

The auto-assign workflow eliminates manual steps in your development process:

- ❌ No more manually creating PRs
- ❌ No more typing "Closes #X" 
- ❌ No more updating project boards
- ✅ Automatic draft PR creation
- ✅ Automatic issue linking
- ✅ Automatic project status updates

Just create a branch with an issue number, push it, and you're ready to code!

---

For questions or issues with this workflow, please check the workflow logs in the Actions tab or open a new issue in the repository.
