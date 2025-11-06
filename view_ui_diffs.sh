#!/bin/bash
# View UI changes side-by-side using git diff

echo "=== Viewing UI Changes from Different Branches ==="
echo ""

# Get the main branch
MAIN_BRANCH=$(cd /Users/user/Desktop/Github/TutorScoring && git branch --show-current)
echo "Current branch: $MAIN_BRANCH"
echo ""

# List branches with UI changes
echo "Available branches to compare:"
git branch | grep -E "(feat-|2025-)" | sed 's/^/  /'

echo ""
echo "Enter the branch name to compare (or press Enter to compare HEAD vs working directory):"
read -r COMPARE_BRANCH

if [ -z "$COMPARE_BRANCH" ]; then
    echo ""
    echo "=== Comparing HEAD vs Working Directory ==="
    git diff HEAD -- frontend/src/ | head -200
else
    echo ""
    echo "=== Comparing $MAIN_BRANCH vs $COMPARE_BRANCH ==="
    git diff $MAIN_BRANCH $COMPARE_BRANCH -- frontend/src/ | head -200
fi

echo ""
echo "=== Summary of Changed Files ==="
if [ -z "$COMPARE_BRANCH" ]; then
    git diff --stat HEAD -- frontend/
else
    git diff --stat $MAIN_BRANCH $COMPARE_BRANCH -- frontend/
fi

