# AI Frontier Monitoring 公开网页 · 发布说明

## 已完成什么

网站第一版已经生成并经过本地自动检查，包括：主页、研究报告第 001 期、16 篇重要论文介绍页、研究主题、方法说明与历史档案。**网页尚未上线**：现有 GitHub 连接不提供「新建仓库 / 开启 Pages」操作，因此这两个步骤需要在网页上操作。

## 第一次发布（推荐）

1. 登录 GitHub，打开 <https://github.com/new>。
2. Owner 选择自己的账户，Repository name 填 `ai-frontier-monitoring-site`，Visibility 必须选 **Public**。新仓库不要引用、导入或复制现有的私有 `ai-frontier-monitoring` 仓库。
3. 下载并解压 **源码包** `ai-frontier-public-site-source-v1.zip`，确保解压后含 `content/`, `scripts/`, `.github/workflows/pages.yml`, `assets/`, `site/` 和 `README.md`。
4. 在本地源码目录打开终端，执行：

   ```bash
   git init
   git branch -M main
   git add .
   git commit -m "Launch public AI frontier research site v1"
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/ai-frontier-monitoring-site.git
   git push -u origin main
   ```

   将 `<YOUR_GITHUB_USERNAME>` 替换为你的 GitHub 用户名。**请勿将整个私有仓库复制过去。**
5. 进入新仓库 **Settings → Pages → Build and deployment → Source → GitHub Actions**。
6. 进入 **Actions**，观察 `Build and deploy public research site` 工作流成功完成；然后在 **Settings → Pages → Visit site** 查看实际网址。

> GitHub Pages 需要仓库存在且工作流实际成功运行后才有可验证的网址。这里不提前承诺一个已经上线的链接。

## 后续更新

- 添加精选论文：编辑 `content/papers.json`，填写题目、DOI、期刊、研究主题、简短结论、意义和限制。不要粘贴整篇摘要或内部 GPT 分析。
- 新增报告：当前首期用 `content/issue.json` 配置。第二期需扩展生成器支持多期报告（在 V2 迭代）。目前可稳定更新第一期文案和重要文献。
- 本地检查：`python scripts/build.py`，`python scripts/check.py`。
- 提交经人工核对的内容，GitHub Actions 会构建并发布。
- 私有项目负责采集与内部审查；公开网站发布要经过**单独的编辑选择**，不建立自动拉取私有源数据的工作流。

## 发布之前复核

- 确保公开内容和措辞符合教授/团队对署名和对外发布的要求。
- 核对高风险数字、论文类型以及 DOI 目标是否正确。
- 不发布真实患者数据、内部稿件、个人联系方式、私有 Drive 链接或访问凭据。
- 如果希望以后固定双周自动发布，建议先建立编辑审核 PR 工作流，而不是无审批直接上线。
