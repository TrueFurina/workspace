#!/usr/bin/env bash
# ============================================================
# 多智能体协同高校科研助理平台 —— 一键启动脚本（A-1 路径）
#
# 形态：WorkBuddy / CodeBuddy 原生 --agents 编排
#       配置：agents_official.json（8 角色，官方字段规范）
#       主 Agent：orchestrator（自主 Triage + 自主分派）
# R5 红线：本脚本只传参数，不做任何调度/校验逻辑
# ============================================================
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS="$HERE/agents_official.json"
MODEL="${CB_MODEL:-deepseek-v3-2-volc}"

usage() {
cat <<'EOF'
用法：
  ./run_platform.sh "自然语言科研任务"          # 自动 Triage（推荐）
  ./run_platform.sh -l "任务"                   # 强制 L 档（跳过评估，最快）
  ./run_platform.sh -m "任务"                   # 强制 M 档（完整链路+评估）
  ./run_platform.sh -h "任务"                   # 强制 H 档（完整链路+评估+鲶鱼，约 16 分钟）
  ./run_platform.sh --check                     # 只校验配置合法性，不跑

环境变量：
  CB_MODEL=模型ID     默认 deepseek-v3-2-volc
  CB_SANDBOX=1        把执行关进 Docker/Podman 容器（更安全，需本机有 docker）

注意：非交互 -p 模式下子 Agent 的 Bash/Write 默认会卡权限审批导致断链，
      脚本已自动加 --subagent-permission-mode bypassPermissions。
      若你在不可信环境使用，请务必配合 CB_SANDBOX=1。
EOF
}

# ---- 只校验 ----
if [[ "${1:-}" == "--check" ]]; then
  python3 - "$AGENTS" <<'PY'
import json,sys
raw=json.load(open(sys.argv[1]))
d={k:v for k,v in raw.items() if not k.startswith("_")}   # _ 开头为注释键，运行时剔除
req={"description","prompt"}; opt={"tools","disallowedTools","model","mcpServers"}
bad=[]
for n,c in d.items():
    if not isinstance(c,dict): bad.append(f"{n}: 不是对象"); continue
    miss=req-set(c)
    if miss: bad.append(f"{n}: 缺 {miss}")
    unk=set(c)-req-opt
    if unk: bad.append(f"{n}: 未知字段 {unk}（官方不认，会被忽略）")
    if not isinstance(c.get("description",""),str) or len(c.get("description",""))<10:
        bad.append(f"{n}: description 过短（编排中枢靠它判断何时分派）")
print(f"角色数: {len(d)}  ->  {', '.join(d)}")
print("\n".join("❌ "+b for b in bad) if bad else "✅ 配置合法（符合 --agents 官方字段规范）")
sys.exit(1 if bad else 0)
PY
  exit $?
fi

# ---- 档位 ----
FORCE=""
TURNS=40
while [[ $# -gt 0 ]]; do
  case "$1" in
    -l) FORCE="请按 L 档处理。"; TURNS=20; shift ;;
    -m) FORCE="请按 M 档处理（完整链路 + 评估）。"; TURNS=45; shift ;;
    -H|-h) FORCE="请按 H 档处理（完整链路 + 评估 + 强制鲶鱼对抗复核）。"; TURNS=90; shift ;;
    --turns) TURNS="$2"; shift 2 ;;
    --help) usage; exit 0 ;;
    *) break ;;
  esac
done

TASK="${*:-}"
if [[ -z "$TASK" ]]; then echo "❌ 缺任务。"; usage; exit 1; fi
[[ -f "$AGENTS" ]] || { echo "❌ 找不到 $AGENTS"; exit 1; }

echo "────────────────────────────────────────────"
echo " 平台：多智能体协同高校科研助理平台（A-1）"
echo " 编排：WorkBuddy 原生 --agents（无自研调度内核）"
echo " 主Agent：orchestrator ｜ 模型：$MODEL ｜ max-turns：$TURNS"
echo " 任务：$TASK"
echo "────────────────────────────────────────────"

# 剔除 _ 开头的注释键后再传给 --agents（官方只认 {name:{description,prompt,...}}）
AGENTS_CLEAN="$(python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
print(json.dumps({k:v for k,v in d.items() if not k.startswith('_')}, ensure_ascii=False))
" "$AGENTS")"

# 权限：非交互 -p 模式下子 Agent 的 Bash/Write 会卡审批，必须显式放行
#   --subagent-permission-mode  放行子 Agent（关键！否则 ③④⑤⑥ 会断链）
#   --permission-mode acceptEdits 放行主 Agent 的文件写入
#   --sandbox container        （可选）把执行关进 Docker/Podman 容器，更安全
# 实测：主 agent 用 acceptEdits 仍会卡 Bash，必须用 bypassPermissions
PERM_ARGS=(--permission-mode bypassPermissions --subagent-permission-mode bypassPermissions)
if [[ "${CB_SANDBOX:-0}" == "1" ]]; then
  PERM_ARGS+=(--sandbox container)
  echo " 隔离：Docker/Podman 容器沙箱"
fi

codebuddy -p \
  --agents "$AGENTS_CLEAN" \
  --agent orchestrator \
  --model "$MODEL" \
  --max-turns "$TURNS" \
  "${PERM_ARGS[@]}" \
  "${FORCE}${TASK}"
