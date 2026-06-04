# claude-sdk-subscription-demo

用 **Claude Agent SDK** + **订阅鉴权**（Claude Pro/Max，不走 API key、不按 token 计费）跑一个最小 agent：
让 Claude 写一个 `fib_demo.py`、用 Bash 工具执行、把输出回报。

## 工作原理（为什么不用配 endpoint）

`claude_agent_sdk` 不直接连模型。`query(...)` 会把 **`claude` CLI 当子进程拉起来**，由 CLI 负责鉴权和 endpoint：

- `ANTHROPIC_API_KEY` **不设** → CLI 读 `~/.claude/.credentials.json` 的 OAuth 凭据，走你的订阅。
- `ClaudeAgentOptions` 里**没有 endpoint/base_url 参数**，无需也无法指定。
- 只有要走自建网关/代理时，才用环境变量 `ANTHROPIC_BASE_URL`（+ `ANTHROPIC_API_KEY`）——但那样就**脱离订阅、变成 API 计费**。

## 前置条件

1. **Python 3.10+**
2. **Claude Code CLI** 已安装并登录订阅，且位于 `~/.local/bin/claude`
   （`demo.py` 里 `cli_path` 是硬编码这个路径；换路径就改 `demo.py` 或删掉那行走 PATH）
   - 验证：`claude --version` 能输出，且 `~/.claude/.credentials.json` 存在
3. **`ANTHROPIC_API_KEY` 必须 unset**（脚本会自检，设了就直接退出）

## 运行

```bash
./run.sh
```

`run.sh` 会自动建 `.venv`、装 `requirements.txt`、unset API key 再跑。

### 手动方式

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
unset ANTHROPIC_API_KEY
.venv/bin/python demo.py
```

## 预期输出（节选）

```
[system] session started · model=claude-opus-4-8 · tools=30 · cwd=.../workspace
[tool-use] Write input={'file_path': '.../workspace/fib_demo.py', ...}
[tool-use] Bash input={'command': 'python3 fib_demo.py', ...}
[tool-result] INFO: computing fibonacci
              INFO: fibonacci numbers: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
              SUM=88
--- session ended ---  subtype: success
```

## 说明

- 生成的脚本写在 `workspace/` 子目录（`cwd`），已被 `.gitignore` 忽略。
- 结束时打印的 `total_cost_usd` 在订阅模式下只是**折算等效价**，不是真实 API 扣费。
- `permission_mode="bypassPermissions"`：agent 在 `workspace/` 里自动执行工具、不再询问。仅适合受控/沙箱目录。
