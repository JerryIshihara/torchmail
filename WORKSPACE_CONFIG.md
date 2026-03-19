# Workspace Configuration

## Project Location
**Correct Location**: `/home/j_ishihara1997/.openclaw/shared-workspace/projects/torchmail/`

**Incorrect Locations** (DO NOT USE):
- `~/.openclaw/workspace-deepseek/projects/torchmail/`
- Any personal workspace directories

## Development Instructions

### 1. Always Navigate to Correct Location
```bash
cd /home/j_ishihara1997/.openclaw/shared-workspace/projects/torchmail
```

### 2. Verify You're in the Right Place
```bash
# Check current directory
pwd
# Should output: /home/j_ishihara1997/.openclaw/shared-workspace/projects/torchmail

# Check git remote
git remote -v
# Should show: https://github.com/JerryIshihara/torchmail.git
```

### 3. Development Workflow
```bash
# 1. Navigate to correct location
cd /home/j_ishihara1997/.openclaw/shared-workspace/projects/torchmail

# 2. Pull latest changes
git pull origin main

# 3. Create feature branch
git checkout -b feature/your-feature-name

# 4. Make changes and commit
git add .
git commit -m "feat: description of changes"

# 5. Push to remote
git push origin feature/your-feature-name

# 6. Create PR on GitHub
```

### 4. Submodule Management
This project is a submodule of the shared workspace. To update the submodule reference:

```bash
# In the shared workspace root
cd /home/j_ishihara1997/.openclaw/shared-workspace

# Update submodule to latest commit
cd projects/torchmail
git pull origin main
cd ..
git add projects/torchmail
git commit -m "chore: update torchmail submodule to latest"
git push origin main
```

## Project Structure Verification
Always verify the project structure contains:
- `README.md` with SaaS description
- `docs/product-management/` with workflow templates
- `package.json` with development scripts
- Proper git configuration pointing to correct repository

## Common Mistakes to Avoid
1. **❌ Working in personal workspace** - Always use shared workspace
2. **❌ Creating duplicate repositories** - Use the existing submodule
3. **❌ Forgetting to update submodule reference** - Update parent repository after changes
4. **❌ Direct commits to main branch** - Use feature branches and PRs

## Quick Reference
```bash
# Correct project path
PROJECT_PATH="/home/j_ishihara1997/.openclaw/shared-workspace/projects/torchmail"

# Always use this alias
alias torchmail="cd $PROJECT_PATH"

# Add to your ~/.bashrc or ~/.zshrc
echo 'alias torchmail="cd /home/j_ishihara1997/.openclaw/shared-workspace/projects/torchmail"' >> ~/.bashrc
source ~/.bashrc
```

## Git Configuration Check
Run this script to verify correct setup:
```bash
#!/bin/bash
EXPECTED_PATH="/home/j_ishihara1997/.openclaw/shared-workspace/projects/torchmail"
EXPECTED_REMOTE="https://github.com/JerryIshihara/torchmail.git"

if [ "$(pwd)" != "$EXPECTED_PATH" ]; then
  echo "❌ Wrong location! Navigate to: $EXPECTED_PATH"
  exit 1
fi

REMOTE=$(git remote get-url origin 2>/dev/null)
if [ "$REMOTE" != "$EXPECTED_REMOTE" ]; then
  echo "❌ Wrong git remote! Expected: $EXPECTED_REMOTE"
  exit 1
fi

echo "✅ Correct workspace configuration"
```

## Support
If you encounter workspace issues:
1. Check this document first
2. Verify you're in the correct directory
3. Check git remote configuration
4. Contact project maintainer if issues persist