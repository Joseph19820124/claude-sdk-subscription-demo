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

# 需要 claude CLI；demo.py 里硬编码 ~/.local/bin/claude
if [ ! -x "$HOME/.local/bin/claude" ]; then
  echo "警告: 未找到 $HOME/.local/bin/claude —— 请先安装 Claude Code CLI 并登录订阅" >&2
fi

exec "$VENV/bin/python" demo.py
