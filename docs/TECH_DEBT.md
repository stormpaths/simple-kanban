# Technical Debt Backlog

**Last Updated:** October 10, 2025

---

## 🔴 High Priority

### Code Linting Issues
**Status:** Identified but not blocking  
**Created:** October 10, 2025  
**Effort:** 4-6 hours

**Description:**
Flake8 linting reveals several code quality issues that should be addressed:

**Issues Found:**
- **F821** - Undefined names in model relationships (forward references)
- **F401** - Unused imports across multiple files
- **E712** - Comparison to True/False (should use `is True` or just `if cond:`)
- **E501** - Lines exceeding 120 characters (a few cases)
- **F841** - Unused variables
- **W291** - Trailing whitespace

**Files Affected:**
- `src/api/*.py` - Unused imports, comparison issues
- `src/models/*.py` - Forward reference issues (F821)
- `src/auth/*.py` - Unused imports, redefinitions
- `tests/frontend/*.py` - Various issues (already ignored in .flake8)

**Current Workaround:**
- Created `.flake8` config to ignore test file issues
- Linting runs but exits with errors
- Does not block development or deployment

**Recommended Fix:**
1. Fix F821 by using proper string forward references in SQLAlchemy models
2. Remove unused imports (F401)
3. Fix comparison operators (E712)
4. Clean up trailing whitespace (W291)
5. Break long lines or adjust max-line-length

**Benefits:**
- Cleaner codebase
- Better IDE support
- Easier code reviews
- Catches potential bugs

**References:**
- `.flake8` configuration file
- `MAKEFILE_FIXES.md` - Initial discovery

---

## 🟡 Medium Priority

### Frontend Modularization
**Status:** Deferred by design  
**Created:** October 4, 2025  
**Effort:** 8-12 hours

**Description:**
`static/js/app.js` is 830 lines - could be modularized into separate components.

**Note:** admin.html kept inline by design for security/simplicity.

**Recommended Approach:**
- Split into modules: auth.js, boards.js, tasks.js, ui.js
- Use ES6 modules
- Maintain current functionality

---

## 🟢 Low Priority

### API Caching Layer
**Status:** Not implemented  
**Created:** October 4, 2025  
**Effort:** 6-8 hours

**Description:**
No caching layer for frequently accessed data (boards, tasks).

**Recommended Approach:**
- Redis caching for board/task data
- Cache invalidation on updates
- TTL-based expiration

---

### Query Optimization
**Status:** Basic optimization done  
**Created:** October 4, 2025  
**Effort:** 4-6 hours

**Description:**
N+1 queries addressed but could optimize further with better eager loading.

---

### Structured Logging
**Status:** Basic logging in place  
**Created:** October 4, 2025  
**Effort:** 3-4 hours

**Description:**
Could enhance logging with structured format (JSON) for better observability.

---

### Configuration Validation
**Status:** Basic validation exists  
**Created:** October 4, 2025  
**Effort:** 2-3 hours

**Description:**
Could add more comprehensive validation for environment variables and config.

---

## 📝 Notes

### Prioritization Criteria
- **High:** Affects code quality, maintainability, or has many occurrences
- **Medium:** Improves architecture or performance
- **Low:** Nice-to-have enhancements

### When to Address
- **High:** Next dedicated refactoring session
- **Medium:** When working in related areas
- **Low:** When time permits or becomes necessary

---

## ✅ Completed Items

### Containerized Testing (October 10, 2025)
- ✅ Containerized `make format` command
- ✅ Containerized `make lint` command (runs but has issues)
- ✅ Updated `make test` to run full test suite
- ✅ Created `.flake8` configuration

### Security Hardening (October 4, 2025)
- ✅ JWT security validation
- ✅ Rate limiting middleware
- ✅ CSRF protection
- ✅ Security headers

### Testing Infrastructure (October 4, 2025)
- ✅ Comprehensive authentication testing
- ✅ Frontend E2E testing
- ✅ Automated testing in CI/CD

---

**Last Review:** October 10, 2025  
**Next Review:** When starting new feature work or refactoring session
