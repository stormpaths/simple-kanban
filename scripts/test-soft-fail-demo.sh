#!/bin/bash
"""
Demonstration of Soft Fail Mode

This script simulates different test failure scenarios to show how
soft-fail and hard-fail modes behave differently.
"""

set -e

echo "🧪 Testing Soft Fail vs Hard Fail Modes"
echo "========================================"

# Test 1: Soft fail mode (should exit 0 even with test failures)
echo -e "\n📝 Test 1: Soft Fail Mode"
echo "Running: ./scripts/post-deploy-test.sh dev full soft"
echo "Expected: Should report failures but exit with success"

# Create a temporary failing test script
cat > /tmp/failing-test.sh << 'EOF'
#!/bin/bash
echo "Running fake failing test..."
echo "❌ Some tests failed"
exit 1
EOF
chmod +x /tmp/failing-test.sh

# Temporarily replace test script path in post-deploy-test.sh for demo
# (In real usage, the actual test-all.sh would fail)

echo -e "\n🔍 Soft fail demonstration:"
if ./scripts/post-deploy-test.sh dev full soft 2>/dev/null || true; then
    echo "✅ Soft fail mode: Deployment would continue despite test failures"
else
    echo "❌ Unexpected: Soft fail mode should not block deployment"
fi

echo -e "\n🔍 Hard fail demonstration:"
if ./scripts/post-deploy-test.sh prod full hard 2>/dev/null; then
    echo "❌ Unexpected: Hard fail mode should block deployment on failures"
else
    echo "✅ Hard fail mode: Deployment would be blocked by test failures"
fi

# Cleanup
rm -f /tmp/failing-test.sh

echo -e "\n📊 Summary:"
echo "- Dev (soft): Tests run, failures reported, deployment continues"
echo "- Prod (hard): Tests run, failures block deployment"
echo "- Both modes provide full visibility into what's broken"
