# mimotion

mimotion 是一个用 GitHub Actions 自动运行的 Zepp Life / 小米运动步数同步脚本。

它做的事情很简单：到点以后，GitHub 会临时启动一台运行环境，拉取这个仓库的代码，执行 `python main.py`。脚本会读取你配置好的 Zepp Life 账号，登录后把当天步数提交到 Zepp/华米接口。如果你的 Zepp Life 已经绑定了微信运动、支付宝运动等第三方平台，后续步数就有机会被这些平台同步过去。

换句话说，它不是直接修改微信数据，也不需要你自己买服务器。它只是把 Python 脚本交给 GitHub Actions 定时执行。

> 使用前请确认你只操作自己的账号。账号、密码、PAT、AES_KEY 都是敏感信息，不要写进公开代码，也不要发到 issue、截图或日志里。

## 这个项目适合谁

如果你希望每天自动给自己的 Zepp Life / 小米运动账号同步一个步数，并且愿意花几分钟配置 GitHub Actions，这个项目就够用了。

如果你是第一次接触 GitHub Actions，也没关系。下面的教程会按“先理解，再配置，再试运行”的顺序来写。

## 它大概怎么工作

整个过程可以这样理解：

```text
GitHub Actions 定时触发
-> GitHub 启动临时 Ubuntu 环境
-> 拉取本仓库代码
-> 安装 Python 依赖
-> 读取 GitHub Secrets 里的 CONFIG / AES_KEY
-> 登录 Zepp Life / 小米运动
-> 计算本次步数
-> 提交步数到 Zepp/华米接口
-> 保存加密 token，减少下次重复登录
-> 随机调整下一次运行的分钟数
```

GitHub Actions 的运行环境是临时的，不是一直在线的服务器。每次任务开始时 GitHub 分配一台机器，任务结束后机器就销毁。

## 功能

- 支持邮箱账号和中国手机号账号。
- 支持多个账号。
- 支持 GitHub Actions 定时运行。
- 支持手动运行 workflow。
- 支持 `DRY_RUN` 试运行，不真正提交步数。
- 支持随机步数和固定步数。
- 支持 AES 加密缓存登录 token。
- 支持 PushPlus 推送运行结果。
- 支持本地 `config.local.json` 调试。
- 支持 `--check-config` 先检查配置。

## 使用前准备

你需要准备这些东西：

- 一个 GitHub 账号。
- 一个已经能正常登录的 Zepp Life / 小米运动账号。
- Fork 后的 mimotion 仓库。
- 一个 GitHub Personal Access Token，后文简称 `PAT`。
- 一个 16 字节的 `AES_KEY`，用来加密保存 token。

这里的 Zepp Life / 小米运动账号，不是“小米账号”的同义词。请使用能在 Zepp Life / 小米运动里登录的手机号或邮箱账号。

## 第一步：Fork 仓库

打开项目页面，点击右上角 `Fork`，把仓库复制到你自己的 GitHub 账号下。

后面的所有设置，都在你 Fork 之后的仓库里完成。

## 第二步：启用 GitHub Actions

进入你自己的仓库，点击 `Actions`。

如果 GitHub 提示你需要确认启用 workflow，点击确认即可。

本项目主要有两个 workflow：

- `MiMotion`：真正执行登录、计算步数、提交步数。
- `Random Cron`：在 `MiMotion` 成功后，随机修改下一次执行的分钟数。

第一次配置完成后，建议先手动运行 `MiMotion` 测试。

## 第三步：创建 PAT

`PAT` 的作用是让 GitHub Actions 有权限把运行中产生的文件提交回仓库，例如：

- `encrypted_tokens.data`
- `.github/workflows/run.yml`
- `cron_change_time`

推荐创建 Fine-grained token。

创建位置：

```text
GitHub -> Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens
```

建议权限：

| 项目 | 建议设置 |
| --- | --- |
| Repository access | 只选择你的 mimotion 仓库 |
| Actions | Read and write |
| Contents | Read and write |
| Metadata | Read-only |
| Workflows | Read and write |

创建完成后复制 token。这个 token 只会显示一次。

## 第四步：配置 Secrets

进入仓库：

```text
Settings -> Secrets and variables -> Actions -> Repository secrets
```

添加下面三个 Secret：

| 名称 | 必填 | 说明 |
| --- | --- | --- |
| `CONFIG` | 是 | 项目运行配置，JSON 格式 |
| `AES_KEY` | 推荐 | 16 字节密钥，用于加密缓存 token |
| `PAT` | 是 | 允许 Actions 自动提交文件 |

### AES_KEY

`AES_KEY` 必须是 16 字节字符串，例如：

```text
1234567890abcdef
```

不要使用中文。长度不对时，脚本会跳过 token 缓存。

### CONFIG

第一次使用建议先开启 `DRY_RUN`：

```json
{
  "USER": "abc@example.com",
  "PWD": "your_password",
  "MIN_STEP": "18000",
  "MAX_STEP": "25000",
  "STEP_MODE": "random",
  "PUSH_PLUS_TOKEN": "",
  "PUSH_PLUS_HOUR": "",
  "PUSH_PLUS_MAX": "30",
  "SLEEP_GAP": "5",
  "USE_CONCURRENT": "False",
  "DRY_RUN": "True"
}
```

确认登录和配置都没问题后，再把 `DRY_RUN` 改成 `False`。

## 配置字段说明

| 字段 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `USER` | 是 | 无 | Zepp Life / 小米运动账号 |
| `PWD` | 是 | 无 | Zepp Life / 小米运动密码 |
| `MIN_STEP` | 否 | `18000` | 随机模式下的目标最小步数 |
| `MAX_STEP` | 否 | `25000` | 随机模式下的目标最大步数 |
| `STEP_MODE` | 否 | `random` | 步数模式，支持 `random` 或 `fixed` |
| `FIXED_STEP` | 固定模式必填 | 无 | 固定模式下提交的步数 |
| `PUSH_PLUS_TOKEN` | 否 | 空 | PushPlus token，不填则不推送 |
| `PUSH_PLUS_HOUR` | 否 | 空 | 只在北京时间指定整点推送 |
| `PUSH_PLUS_MAX` | 否 | `30` | 推送里展示账号详情的最大账号数 |
| `SLEEP_GAP` | 否 | `5` | 多账号非并发模式下的间隔秒数 |
| `USE_CONCURRENT` | 否 | `False` | 多账号是否并发执行 |
| `DRY_RUN` | 否 | `False` | 是否只登录和计算步数，不提交步数 |

## 多账号写法

多个账号用 `#` 分隔，密码也要用 `#` 分隔，并且数量必须一致。

```json
{
  "USER": "user1@example.com#user2@example.com",
  "PWD": "password1#password2",
  "MIN_STEP": "18000",
  "MAX_STEP": "25000",
  "STEP_MODE": "random",
  "SLEEP_GAP": "8",
  "USE_CONCURRENT": "False",
  "DRY_RUN": "True"
}
```

如果账号和密码数量不一致，脚本会在启动时直接提示错误。

## 步数怎么计算

### random：随机模式

默认是随机模式：

```json
{
  "STEP_MODE": "random",
  "MIN_STEP": "18000",
  "MAX_STEP": "25000"
}
```

随机模式不是一大早就直接刷到 18000 到 25000。脚本会按北京时间做比例缩放，越接近 22:00，随机范围越接近完整的 `MIN_STEP` 到 `MAX_STEP`。

这样做是为了让步数看起来更像一天慢慢增加，而不是早上突然跳到很高。

### fixed：固定模式

固定模式适合第一次测试，也适合你希望每次都提交同一个步数的情况：

```json
{
  "STEP_MODE": "fixed",
  "FIXED_STEP": "20000"
}
```

固定模式下，`MIN_STEP` 和 `MAX_STEP` 不参与本次计算。

## 第五步：第一次手动运行

进入仓库 `Actions` 页面，选择 `MiMotion`，点击 `Run workflow`。

手动运行时有一个 `dry_run` 选项：

- `true`：只登录和计算步数，不提交。
- `false`：正常执行。

第一次建议选 `true`。

运行后，进入最新的 workflow 记录，展开 `Run MiMotion` 看日志。

如果看到类似：

```text
DRY_RUN 已开启：会验证登录并计算步数，但不会提交步数
执行账号总数：1，成功：1，失败：0
```

说明配置基本正确。

然后你可以把 `CONFIG` 里的 `DRY_RUN` 改成 `False`，再运行一次正式提交。

## 默认每天几点运行

默认定时配置在：

```text
.github/workflows/run.yml
```

当前默认 cron 是：

```yaml
cron: '25 1,7,10,12,14,23 * * *'
```

GitHub Actions 使用 UTC 时间。换算成北京时间大约是：

```text
09:25
15:25
18:25
20:25
22:25
07:25
```

不过 `Random Cron` 会在主任务成功后随机修改分钟数，所以实际执行可能不是一直卡在 `25` 分。

如果想改运行小时，可以到：

```text
Settings -> Secrets and variables -> Actions -> Variables
```

添加变量：

```text
CRON_HOURS=1,7,10,12,14,23
```

这里填的是 UTC 小时，不是北京时间。

## PushPlus 推送

如果你想在运行后收到微信推送，可以去 PushPlus 获取 token，然后写进 `CONFIG`：

```json
{
  "PUSH_PLUS_TOKEN": "your_pushplus_token"
}
```

如果只想在北京时间 22 点推送：

```json
{
  "PUSH_PLUS_HOUR": "22"
}
```

不配置 `PUSH_PLUS_TOKEN` 时，不会推送。

## 本地调试

本地调试适合在正式放到 GitHub Actions 前检查配置，尤其是 JSON 格式和多账号数量。

### 1. 安装依赖

建议 Python 3.10 或更高版本。

```bash
pip install -r requirements.txt
```

### 2. 创建本地配置

复制示例文件：

```bash
cp config.local.example.json config.local.json
```

Windows PowerShell：

```powershell
Copy-Item config.local.example.json config.local.json
```

`config.local.json` 已经在 `.gitignore` 里，不会被提交。

### 3. 检查配置

```bash
python main.py --check-config
```

配置没问题时会显示：

```text
配置检查通过
```

### 4. 本地试运行

```bash
python main.py --dry-run
```

`--dry-run` 会强制试运行，即使配置里 `DRY_RUN` 是 `False`，也不会真正提交步数。

指定配置文件：

```bash
python main.py --config config.local.json --dry-run
```

注意：如果同时存在环境变量 `CONFIG` 和本地配置文件，脚本优先读取环境变量 `CONFIG`。

## 常见问题

### Actions 成功了，但微信步数没变？

这个项目不直接修改微信数据。它提交的是 Zepp Life / 小米运动数据，微信是否更新取决于第三方同步。你可以先检查 Zepp Life 里步数是否变化，再检查微信运动绑定状态。

### 第一次运行提示 token 解密失败？

通常是因为仓库里的 `encrypted_tokens.data` 不是用你的 `AES_KEY` 生成的。第一次遇到可以忽略，成功登录后会重新生成。

### 出现 429 怎么办？

429 多半是请求太频繁。可以这样处理：

- 关闭 `USE_CONCURRENT`。
- 增大 `SLEEP_GAP`。
- 减少同一时间运行的账号数量。
- 过一段时间再手动运行。

### workflow 提交失败？

大概率是 `PAT` 权限不够，重点检查：

- `Contents: Read and write`
- `Workflows: Read and write`
- token 是否授权给当前 Fork 后的仓库
- `PAT` 是否正确保存到了 Repository secrets

### 怎么确认本次用的步数？

日志里会显示：

```text
步数模式：random，本次范围：xxxx~yyyy
```

固定模式会显示：

```text
步数模式：fixed，本次范围：20000~20000
```

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `main.py` | 主入口，负责读取配置、执行账号任务、推送结果 |
| `util/zepp_helper.py` | Zepp/华米接口请求逻辑 |
| `util/aes_help.py` | AES 加密和解密 |
| `requirements.txt` | Python 依赖列表 |
| `config.local.example.json` | 本地调试配置模板 |
| `encrypted_tokens.data` | 加密后的 token 缓存 |
| `.github/workflows/run.yml` | 主定时任务 |
| `.github/workflows/cron.yml` | 随机修改 cron 的任务 |
| `cron_convert.sh` | 修改 cron 的 shell 脚本 |
| `cron_change_time` | 最近一次 cron 修改记录 |

## 参考与致谢

这个项目是在前人工作的基础上继续整理和维护的，核心思路来自社区里多个 mimotion / Zepp Life 刷步项目。感谢这些项目和作者提供的接口思路、参数样例和加密方式参考：

- [TonyJiangWJ/mimotion](https://github.com/TonyJiangWJ/mimotion)
- [huangshihai/mimotion](https://github.com/huangshihai/mimotion)
- 已不可访问的 `xunichanghuan/mimotion`
- [hanximeng/Zepp_API](https://github.com/hanximeng/Zepp_API)

如果这些项目对你有帮助，也可以顺手去原项目点个 star。开源项目能被后来的人继续用下去，很多时候就是靠这种一点点的接力。
