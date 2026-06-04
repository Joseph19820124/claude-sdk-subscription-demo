#!/usr/bin/env bash
# 一键运行：建/复用 venv、装依赖、用订阅鉴权跑 demo。
set -euo pipefail
cd "$(dirname "$0")"

VENV=".venv"
[ -d "$VENV" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r requirements.txt

# 订阅模式：必须确保没有 API key，否则会变成按 token 计费
unset ANTHROPIC_API_KEY ANTHROPIC_BASE_URL

# 需要 claude CLI：先看 PATH（兼容 Homebrew、apt 等安装方式），
# 再看 ~/.local/bin/claude 这个用户态默认路径。两个都没就警告。
if command -v claude >/dev/null 2>&1; then
  echo "找到 claude: $(command -v claude)" >&2
elif [ -x "$HOME/.local/bin/claude" ]; then
  echo "找到 claude: $HOME/.local/bin/claude (PATH 中没有，将由 demo.py 显式传入)" >&2
else
  echo "警告: 未找到 claude CLI —— 请先安装 Claude Code 并 \`claude login\` 完成订阅鉴权" >&2
fi

exec "$VENV/bin/python" demo.py
