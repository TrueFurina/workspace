#!/bin/bash
# ============================================================
# 国创赛2026 交付物 · 本机一键推送到 GitHub
# 适用：你本机（macOS / Linux / WSL）运行本脚本。
# 原因：WorkBuddy 沙箱无法直连 GitHub 公网（实测 github.com 被 DNS 黑洞，
#       全端口不可达 / TLS 中断），故由你本机执行此脚本完成推送。
# 用法：
#   export GITHUB_TOKEN=ghp_你的PAT      # 方式A：用 PAT 鉴权（无需本机登录）
#   bash push_to_github.sh               # 默认推到 TrueFurina/workspace
#   bash push_to_github.sh owner/repo    # 指定其他仓库
# 不设置 GITHUB_TOKEN 时，回退到本机已登录的 gh / credential / ssh。
# ============================================================
set -e

REPO="${1:-TrueFurina/workspace}"
SUBDIR="国创赛2026交付物"
WORKDIR="$(cd "$(dirname "$0")" && pwd)"

echo "源目录   : $WORKDIR"
echo "目标仓库 : $REPO"

# 鉴权：优先用 GITHUB_TOKEN（PAT），否则依赖本机已登录的 GitHub
if [ -n "${GITHUB_TOKEN:-}" ]; then
  REMOTE="https://oauth2:${GITHUB_TOKEN}@github.com/${REPO}.git"
  echo "鉴权方式 : GITHUB_TOKEN (PAT)"
else
  REMOTE="https://github.com/${REPO}.git"
  echo "鉴权方式 : 本机 GitHub 登录 (gh / credential / ssh)"
fi

# 1) 克隆目标仓库到临时目录
TMP="$(mktemp -d)"
echo "克隆 $REPO ..."
if git clone "$REMOTE" "$TMP" 2>/dev/null; then
  BRANCH="$(cd "$TMP" && git rev-parse --abbrev-ref HEAD)"
else
  echo "克隆失败（仓库可能为空或需鉴权）→ 初始化空仓库后推送"
  git init "$TMP" >/dev/null
  git -C "$TMP" remote add origin "$REMOTE"
  BRANCH="$(cd "$TMP" && git branch --show-current 2>/dev/null || true)"
  [ -z "$BRANCH" ] && BRANCH=main
fi
echo "分支     : $BRANCH"

# 2) 把本包内容放进子目录（不覆盖仓库根目录已有文件）
mkdir -p "$TMP/$SUBDIR"
echo "复制交付物到 $SUBDIR/ ..."
cp -r "$WORKDIR"/. "$TMP/$SUBDIR"/

# 3) 提交并推送
cd "$TMP"
git config user.email "delivery@workbuddy.local"
git config user.name "国创赛交付机器人"
git add -A
if git diff --cached --quiet; then
  echo "无变更，无需提交"
else
  git commit -m "归档: 国创赛2026 多智能体科研助理平台 交付物 $(date +%Y-%m-%d)"
  git push -u origin "$BRANCH"
  echo "已推送到 https://github.com/${REPO} (分支 $BRANCH, 目录 ${SUBDIR}/)"
fi
cd /
rm -rf "$TMP"
echo "完成。"
