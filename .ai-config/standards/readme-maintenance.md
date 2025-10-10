# README Maintenance Standard

**Purpose:** Ensure README.md always reflects the current state of the project

---

## 📋 **Core Principle**

> **The README is the source of truth for how to use the project.**  
> It must be updated whenever commands, features, or workflows change.

---

## ✅ **When to Update README**

### **ALWAYS Update When:**

1. **Adding/Changing Commands**
   - New Makefile targets
   - Modified CLI commands
   - Changed script usage
   - Updated environment variables

2. **Adding/Removing Features**
   - New functionality
   - Deprecated features
   - Changed workflows
   - Modified APIs

3. **Changing URLs/Endpoints**
   - Production URLs
   - Development URLs
   - API endpoints
   - Documentation links

4. **Updating Dependencies**
   - New required tools
   - Changed versions
   - New prerequisites
   - Installation steps

5. **Modifying Testing**
   - New test commands
   - Changed test coverage
   - Updated test procedures
   - New test categories

6. **Changing Deployment**
   - New deployment steps
   - Modified CI/CD
   - Changed environments
   - Updated configurations

---

## 📝 **What to Document**

### **1. Quick Start Section**
```markdown
## Quick Start

# Most common commands users need
make test              # Primary testing command
make dev               # Start development
make build             # Build the project
```

**Rule:** Show the 3-5 most common commands first

### **2. Testing Section**
```markdown
## Testing

### Quick Start - Makefile Commands
# Show Makefile commands FIRST (primary interface)

### Automated Testing
# Show CI/CD integration

### Manual Testing
# Show script usage (secondary)
```

**Rule:** Primary interface (Makefile) comes before secondary (scripts)

### **3. Environment URLs**
```markdown
**Production URL**: https://example.com
**Development URL**: https://dev.example.com
```

**Rule:** Always document all environment URLs clearly

### **4. Prerequisites**
```markdown
## Prerequisites

- Docker 20.10+
- kubectl 1.28+
- Python 3.11+ (for local development)
```

**Rule:** List exact versions and when each is needed

---

## 🔄 **Update Process**

### **Step 1: Make Code Changes**
```bash
# Make your changes
vim Makefile
vim src/main.py
```

### **Step 2: Update README**
```bash
# Update README to match
vim README.md
```

### **Step 3: Verify**
```bash
# Test that README commands work
make test
make build

# Check for broken links
grep -r "http" README.md
```

### **Step 4: Commit Together**
```bash
# Commit code and README together
git add Makefile README.md
git commit -m "feat: Add new test command

- Added make test-integration
- Updated README with new command
- Documented usage and examples"
```

**Rule:** Code changes and README updates go in the same commit

---

## ❌ **Common Mistakes**

### **1. Outdated Commands**
```markdown
# ❌ BAD - Command no longer exists
pytest tests/

# ✅ GOOD - Current command
make test
```

### **2. Missing New Features**
```markdown
# ❌ BAD - New feature not documented
# (User added make test-backend but didn't update README)

# ✅ GOOD - All commands documented
make test              # All tests
make test-backend      # Backend only
make test-frontend     # Frontend only
```

### **3. Wrong URLs**
```markdown
# ❌ BAD - Old URL
https://old-domain.com

# ✅ GOOD - Current URL
https://kanban.stormpath.net
```

### **4. Incomplete Examples**
```markdown
# ❌ BAD - No context
make test

# ✅ GOOD - With explanation
make test              # Run all tests (backend + frontend)
```

---

## 🎯 **README Sections to Maintain**

### **Critical Sections (Always Update):**
1. **Quick Start** - Most common commands
2. **Testing** - How to run tests
3. **Installation** - Setup steps
4. **Configuration** - Environment variables
5. **Deployment** - How to deploy

### **Important Sections (Update When Changed):**
6. **Features** - What the project does
7. **Architecture** - How it's structured
8. **API Documentation** - Endpoints and usage
9. **Contributing** - How to contribute
10. **Troubleshooting** - Common issues

### **Nice-to-Have Sections:**
11. **Changelog** - Recent changes
12. **Roadmap** - Future plans
13. **Credits** - Contributors
14. **License** - Legal information

---

## 📊 **Verification Checklist**

Before committing, verify:

- [ ] All commands in README actually work
- [ ] URLs are correct and accessible
- [ ] Version numbers are current
- [ ] Examples run successfully
- [ ] No references to removed features
- [ ] New features are documented
- [ ] Prerequisites are accurate
- [ ] Links are not broken

---

## 🔍 **Review Process**

### **Self-Review:**
```bash
# Read README as if you're a new user
# Can you set up and use the project?

# Test every command shown
make test
make build
make deploy
```

### **Automated Checks:**
```bash
# Check for broken links (if you have tools)
markdown-link-check README.md

# Verify command examples
grep "make " README.md | while read cmd; do
    echo "Testing: $cmd"
    $cmd --help || echo "⚠️  Command may be invalid"
done
```

---

## 📚 **Examples of Good Updates**

### **Example 1: Adding New Command**
```markdown
# Commit message
feat: Add make test-backend command

- Added test-backend target to Makefile
- Updated README Testing section
- Added example usage and output
```

### **Example 2: Changing URLs**
```markdown
# Commit message
fix: Update production URL in README

- Changed from old-domain.com to new-domain.com
- Updated all references in Testing section
- Verified URL is accessible
```

### **Example 3: Deprecating Feature**
```markdown
# Commit message
refactor: Remove old test script

- Removed test-old.sh script
- Updated README to use make test instead
- Added migration note for existing users
```

---

## 🎓 **Best Practices**

### **1. User-First Perspective**
Write as if the reader knows nothing about the project.

### **2. Show, Don't Tell**
```markdown
# ❌ BAD
You can run tests.

# ✅ GOOD
make test              # Run all tests (93% coverage)
```

### **3. Keep It Current**
```markdown
# ❌ BAD
Last updated: January 2024

# ✅ GOOD
(No "last updated" - README is always current)
```

### **4. Organize by Frequency**
Most common tasks first, advanced topics later.

### **5. Link to Details**
```markdown
See [Testing Guide](docs/testing.md) for advanced options.
```

---

## 🚨 **Red Flags**

Watch for these signs README is outdated:

- ❌ Commands that don't work
- ❌ URLs that return 404
- ❌ Features mentioned that don't exist
- ❌ Missing new features
- ❌ Incorrect version numbers
- ❌ Broken documentation links
- ❌ Old screenshots
- ❌ Deprecated tools mentioned

---

## ✅ **Success Criteria**

A good README:

1. **Works** - Every command runs successfully
2. **Current** - Reflects actual codebase state
3. **Clear** - New users can get started
4. **Complete** - All features documented
5. **Organized** - Easy to find information
6. **Maintained** - Updated with every change

---

## 📝 **Template for Updates**

When updating README, use this checklist:

```markdown
## README Update Checklist

- [ ] Updated Quick Start commands
- [ ] Verified all commands work
- [ ] Updated URLs (prod/dev)
- [ ] Added new features
- [ ] Removed deprecated features
- [ ] Updated version numbers
- [ ] Checked all links
- [ ] Updated examples
- [ ] Tested from user perspective
- [ ] Committed with code changes
```

---

## 🎯 **Summary**

**Golden Rule:**  
> If you change how something works, update the README in the same commit.

**Why This Matters:**
- Users trust the README
- Outdated docs waste time
- README is often the first impression
- Good docs = good project

**Remember:**
- README is not optional
- README is not "nice to have"
- README is not "we'll update it later"
- **README is part of the feature**

---

**Last Updated:** October 10, 2025  
**Status:** Active Standard  
**Applies To:** All projects in stormpath organization
