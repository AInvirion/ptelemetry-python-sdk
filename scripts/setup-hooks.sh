#!/bin/bash
# Install git hooks

git config core.hooksPath .githooks
chmod +x .githooks/pre-push
echo "✅ Git hooks installed. Codex will run before every push."
