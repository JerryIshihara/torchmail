# Pull Request Process for TorchMail

## Overview
This document outlines the standard Pull Request (PR) process for TorchMail development. All code changes should go through this PR process to ensure quality, consistency, and proper documentation.

## PR Creation Workflow

### 1. Branch Naming Convention
```
feature/<short-description>    # New features
bugfix/<issue-number>          # Bug fixes
docs/<description>             # Documentation updates
refactor/<description>         # Code refactoring
test/<description>             # Test additions
```

### 2. Creating a PR
```bash
# 1. Create and switch to feature branch
git checkout -b feature/your-feature-name

# 2. Make your changes and commit
git add .
git commit -m "feat: description of changes"

# 3. Push to remote
git push origin feature/your-feature-name

# 4. Create PR using GitHub CLI
gh pr create --title "feat: Your feature title" --body "Description of changes"

# Or create via GitHub UI
# Visit: https://github.com/JerryIshihara/torchmail/pull/new/feature/your-feature-name
```

### 3. PR Template
Every PR should include:

#### Title Format
```
<type>: <description>
```
Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

#### PR Description Template
```markdown
## 🎯 What does this PR do?
Brief description of changes

## 📋 Related Issues
Closes #<issue-number>
Fixes #<issue-number>

## 🧪 Testing
- [ ] Unit tests added/updated
- [ ] Integration tests passing
- [ ] Manual testing completed
- [ ] Documentation updated

## 📸 Screenshots (if UI changes)
<!-- Add screenshots here -->

## 📊 Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing

## 🔗 References
<!-- Links to related PRs, issues, or documentation -->
```

## PR Review Process

### 1. Required Reviews
- **Minimum 1 reviewer** for all PRs
- **2 reviewers** for:
  - Core architecture changes
  - Security-related changes
  - Database schema changes
  - Major feature implementations

### 2. Review Checklist
Reviewers should check:
- [ ] Code quality and readability
- [ ] Adherence to coding standards
- [ ] Test coverage
- [ ] Documentation updates
- [ ] Performance considerations
- [ ] Security implications
- [ ] Error handling
- [ ] Logging and monitoring

### 3. Review Timeline
- **Small PRs** (< 200 lines): Within 24 hours
- **Medium PRs** (200-500 lines): Within 48 hours
- **Large PRs** (> 500 lines): Within 72 hours

## PR Approval & Merge

### 1. Approval Requirements
- All required reviewers approved
- All checks passing (CI, tests, linting)
- No unresolved comments
- Documentation updated if needed

### 2. Merge Strategies
- **Squash and Merge**: For feature branches (recommended)
- **Rebase and Merge**: For clean history when needed
- **Merge Commit**: For collaborative branches

### 3. Post-Merge Actions
1. Delete the feature branch
2. Update related issues
3. Update documentation if needed
4. Notify relevant team members

## Special PR Types

### Documentation PRs
- Should include before/after examples
- Must be reviewed by documentation owner
- Should update CHANGELOG.md if applicable

### Bug Fix PRs
- Must include steps to reproduce
- Should include test case for the bug
- Should reference the issue being fixed

### Security PRs
- Require security team review
- Should not disclose security details in PR
- May require special handling

## CI/CD Integration

### Automated Checks
Every PR automatically runs:
- **Linting**: ESLint, Prettier
- **Testing**: Unit tests, integration tests
- **Build**: Verify build succeeds
- **Security**: Code scanning, dependency checks

### Required Status Checks
PR cannot be merged until:
- [ ] `ci/lint` passes
- [ ] `ci/test` passes
- [ ] `ci/build` passes
- [ ] `security/scan` passes

## Best Practices

### 1. Keep PRs Small
- Focus on one logical change per PR
- Break large features into multiple PRs
- Aim for < 500 lines of code change

### 2. Write Good Commit Messages
```
feat: add search engine compatibility scoring

- Implement multi-dimensional scoring (skills, research, timing, culture)
- Add ML model for hiring intent prediction
- Update API endpoints for compatibility results

Closes #123
```

### 3. Use Descriptive Titles
- ❌ "Fix bug"
- ✅ "fix: resolve null pointer in search results pagination"

### 4. Include Testing Evidence
- Screenshots for UI changes
- Test output for complex logic
- Performance metrics if applicable

### 5. Update Documentation
- Update README if features change
- Update API documentation
- Update CHANGELOG for user-facing changes

## Troubleshooting

### PR Stuck in Review?
1. Ping reviewers after 24 hours
2. Address all review comments promptly
3. Break into smaller PRs if too large

### CI Checks Failing?
1. Check logs for specific errors
2. Run tests locally before pushing
3. Ask for help if stuck

### Merge Conflicts?
1. Rebase on latest main
2. Resolve conflicts carefully
3. Test after conflict resolution

## Tools & Resources

### GitHub CLI
```bash
# List PRs
gh pr list

# View specific PR
gh pr view <number>

# Checkout PR locally
gh pr checkout <number>

# Add review comment
gh pr review --comment "Looks good!"
```

### VS Code Extensions
- **GitHub Pull Requests**: Manage PRs in VS Code
- **GitLens**: Enhanced git capabilities
- **Code Spell Checker**: Catch typos

### Useful Links
- [GitHub PR Documentation](https://docs.github.com/en/pull-requests)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PR Best Practices](https://github.com/trein/dev-best-practices/wiki/Git-Pull-Request-Best-Practices)

---

*This process ensures consistent quality and collaboration across the TorchMail project.*