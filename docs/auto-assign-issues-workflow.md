# Auto-Assign Issues Workflow

## Overview

The `auto-assign-issues.yml` workflow automatically creates a parent issue that groups related issues mentioned in commit messages. This helps track implementations that address multiple issues simultaneously.

## How It Works

1. **Trigger**: The workflow runs on every push to any branch
2. **Parse**: Extracts issue numbers from the commit message (e.g., `#123`, `#456`)
3. **Fetch**: Retrieves details for each mentioned issue using the GitHub API
4. **Create**: Generates a parent issue with:
   - A descriptive title summarizing the sub-issues
   - A task list linking to all sub-issues
   - Reference to the commit that triggered the workflow
5. **Link**: Adds a comment to each sub-issue linking back to the parent issue

## Usage

Simply include issue numbers in your commit messages using the `#` prefix:

```bash
# Single issue
git commit -m "Fixes #123"

# Multiple issues
git commit -m "Implements #42 and #58, addresses #91"
```

The workflow will:
- For 1 issue: Create a parent issue titled "Implementation of [issue title]"
- For multiple issues: Create a parent issue titled "Implementation of N related issues"

## Example

**Commit message:**
```
Fix database connection and add logging #15 #23
```

**Generated parent issue:**
```
Title: Implementation of 2 related issues

Body:
This issue tracks the implementation of related issues mentioned in commit `abc1234`.

## Sub-Issues

- [ ] #15: Database connection pooling
- [ ] #23: Add comprehensive logging

---

**Commit Message:**
```
Fix database connection and add logging #15 #23
```
```

## Labels

Parent issues are automatically tagged with the `auto-generated` label.

## Permissions

The workflow requires:
- `issues: write` - To create issues and comments
- `contents: read` - To access repository content and commits

## Limitations

- Only processes issues that exist in the repository
- Issues must be referenced using the `#number` format
- Non-existent issue numbers are silently skipped
