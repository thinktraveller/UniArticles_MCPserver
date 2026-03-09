# Tutorial: Project Preparation for GitHub Release / 项目发布准备教程

This document records the steps taken to prepare the UniArticles MCP Server for GitHub release.
本文档记录了 UniArticles MCP Server 准备发布至 GitHub 的操作步骤。

## Step 1: Create .gitignore / 创建 .gitignore
**Why**: To prevent sensitive files (like `.env`) and unnecessary build artifacts from being uploaded to GitHub.
**原因**: 防止敏感文件（如 `.env`）和不必要的构建产物上传到 GitHub。

**Command / 命令**:
```bash
# Handled automatically by the assistant
# 助手已自动处理
```

**Content / 内容**:
- Ignored Python cache files (`__pycache__`, `*.pyc`)
- Ignored virtual environments (`.venv`, `env/`)
- Ignored environment variables (`.env`)
- Ignored build artifacts (`build/`, `dist/`, `*.egg-info/`)
- Ignored IDE settings (`.vscode/`, `.idea/`)
- Ignored project specific files (`arxiv_downloads/`, `*.pdf`)

## Step 2: Merge and Update README.md / 合并并更新 README.md
**Why**: To provide a comprehensive, bilingual guide for users, preserving all original information including acknowledgments.
**原因**: 为用户提供全面、双语的指南，保留包括致谢在内的所有原始信息。

**Changes / 变更**:
- Merged content from the root README and the project README.
- Added "Project Structure" section to both English and Chinese parts.
- Ensured "Acknowledgments" section is present and bilingual.
- Updated License badges and information.

## Step 3: Create Strict License / 创建严格的开源协议
**Why**: To protect the project with a copyleft license (AGPL-3.0) and explicitly restrict commercial use.
**原因**: 使用传染性开源协议 (AGPL-3.0) 保护项目，并明确限制商业使用。

**License Details / 协议详情**:
- **Base License**: GNU Affero General Public License v3.0 (AGPL-3.0)
- **Additional Restriction**: Commercial use requires written authorization.
- **File**: `LICENSE`

## Step 4: Separate Bilingual Documentation / 分离双语文档
**Why**: To improve readability and user experience by providing separate README files for English and Chinese users.
**原因**: 通过为中英文用户提供单独的 README 文件，提高可读性和用户体验。

**Changes / 变更**:
- Created `README_ZH.md` for Chinese content.
- Updated `README.md` to contain English content and a link to the Chinese version.
- Preserved License and Acknowledgments in both files.

## Next Steps / 下一步

You are now ready to initialize the git repository and push to GitHub.
您现在可以初始化 git 仓库并推送到 GitHub。

```bash
$ git init
$ git add .
$ git commit -m "Initial commit: UniArticles MCP Server"
$ git branch -M main
$ git remote add origin https://github.com/your-username/UniArticles_MCPserver.git
$ git push -u origin main
```
