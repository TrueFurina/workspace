# ============================================================
# 国创赛2026 交付物 · Windows 一键推送到 GitHub（PowerShell 版）
# 依赖：本机已安装 Git for Windows（提供 git.exe，且 git 在 PATH 中）
# 用法（PowerShell 窗口，先 cd 到本文件夹）：
#   $env:GITHUB_TOKEN = "ghp_你的PAT"
#   .\push_to_github.ps1                 # 默认 TrueFurina/workspace
#   .\push_to_github.ps1 owner/repo      # 指定其他仓库
# ============================================================
param([string]$Repo="TrueFurina/workspace")

$ErrorActionPreference = "Stop"
$Subdir = "国创赛2026交付物"
$Workdir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $env:GITHUB_TOKEN) {
    Write-Error "请先设置 PAT：`$env:GITHUB_TOKEN = 'ghp_你的PAT'"
    exit 1
}

$remote = "https://oauth2:$($env:GITHUB_TOKEN)@github.com/$Repo.git"
Write-Host "源目录   : $Workdir"
Write-Host "目标仓库 : $Repo"

# 1) 克隆到临时目录
$tmp = Join-Path $env:TEMP ("ghpush_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null
Write-Host "克隆 $Repo ..."
$branch = ""
$null = git clone $remote $tmp 2>&1
if ($LASTEXITCODE -eq 0) {
    $branch = (git -C $tmp rev-parse --abbrev-ref HEAD)
} else {
    Write-Host "克隆失败（仓库可能为空或需鉴权）→ 初始化空仓库后推送"
    git init $tmp | Out-Null
    git -C $tmp remote add origin $remote
    $branch = "main"
}
Write-Host "分支     : $branch"

# 2) 复制交付物到子目录（不覆盖仓库根目录已有文件）
New-Item -ItemType Directory -Path (Join-Path $tmp $Subdir) -Force | Out-Null
Copy-Item "$Workdir\*" -Destination (Join-Path $tmp $Subdir) -Recurse -Force

# 3) 提交并推送
Push-Location $tmp
git config user.email "delivery@workbuddy.local"
git config user.name "国创赛交付机器人"
git add -A
$changes = (git diff --cached --name-only).Count
if ($changes -gt 0) {
    git commit -m "归档: 国创赛2026 多智能体科研助理平台 交付物 $(Get-Date -Format yyyy-MM-dd)" | Out-Null
    git push -u origin $branch
    Write-Host "已推送 https://github.com/$Repo (分支 $branch, 目录 $Subdir/)"
} else {
    Write-Host "无变更，未提交"
}
Pop-Location
Remove-Item $tmp -Recurse -Force
Write-Host "完成。"
