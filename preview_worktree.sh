#!/bin/bash
# Preview UI changes from a worktree on a different port

if [ -z "$1" ]; then
    echo "Usage: ./preview_worktree.sh <worktree-name> [port]"
    echo ""
    echo "Available worktrees:"
    git worktree list | grep -v "/Users/user/Desktop/Github/TutorScoring" | awk '{print "  " $3 " (" $1 ")"}' | tr -d '[]'
    exit 1
fi

WORKTREE_NAME=$1
PORT=${2:-3001}

# Find the worktree path
WORKTREE_PATH=$(git worktree list | grep "$WORKTREE_NAME" | awk '{print $1}')

if [ -z "$WORKTREE_PATH" ]; then
    echo "Error: Worktree '$WORKTREE_NAME' not found"
    exit 1
fi

echo "Starting dev server from worktree: $WORKTREE_NAME"
echo "Worktree path: $WORKTREE_PATH"
echo "Port: $PORT"
echo ""
echo "Access at: http://localhost:$PORT"
echo "Main workspace: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"

cd "$WORKTREE_PATH/frontend" || exit 1

# Check if node_modules exists, if not install
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Create a temporary vite config with different port
cat > vite.config.temp.js <<EOF
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: $PORT,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
EOF

# Run vite with the temp config
npx vite --config vite.config.temp.js

# Cleanup
rm -f vite.config.temp.js

