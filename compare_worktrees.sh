#!/bin/bash
# Script to compare UI changes from different worktrees side-by-side

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Compare Worktrees UI Changes ===${NC}\n"

# Get current worktree
MAIN_WORKTREE="/Users/user/Desktop/Github/TutorScoring"
echo -e "${GREEN}Main workspace:${NC} $MAIN_WORKTREE"
echo -e "${GREEN}Current branch:${NC} $(cd $MAIN_WORKTREE && git branch --show-current)\n"

# List worktrees with UI changes
echo -e "${YELLOW}Available worktrees:${NC}"
git worktree list | grep -v "$MAIN_WORKTREE" | while read -r line; do
    worktree_path=$(echo "$line" | awk '{print $1}')
    branch=$(echo "$line" | awk '{print $3}' | tr -d '[]')
    echo "  - $branch: $worktree_path"
done

echo ""
echo -e "${BLUE}To compare UI changes, you have these options:${NC}\n"
echo -e "${GREEN}Option 1: Run dev servers on different ports${NC}"
echo "  1. Main workspace: http://localhost:3000 (already running)"
echo "  2. Worktree (e.g., 8SIaM): http://localhost:3001"
echo ""
echo -e "${GREEN}Option 2: View git diff directly${NC}"
echo "  Run: git diff HEAD~1 HEAD -- frontend/"
echo ""
echo -e "${GREEN}Option 3: Compare worktree branches${NC}"
echo "  Run: git diff ML_matching_update feat-optimize-ui-space-8SIaM -- frontend/"

