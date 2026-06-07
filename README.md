# mimotion

mimotion 是一个用 GitHub Actions 自动运行的 Zepp Life / 小米运动步数同步脚本。

它不会直接修改微信数据。脚本做的是：登录你的 Zepp Life / 小米运动账号，把当天步数提交到 Zepp/华米接口。如果你的 Zepp Life 已经绑定了微信运动、支付宝运动等平台，后续这些平台可能会同步到新的步数。

项目不需要你买服务器，也不需要电脑每天开着。GitHub Actions 到点后会临时启动一台运行环境，执行仓库里的 Python 脚本，执行完就结束。

> 请只操作你自己的账号。账号、密码、AES_KEY 都是敏感信息，不要写进公开代码，也不要发到截图、issue 或日志里。

## 先看这里：不要直接点开 HTML 文件

如果你在 GitHub 里点击 `config-generator.html`，看到的是满屏代码，这是正常的。GitHub 默认把 HTML 文件当源码展示，不会直接当网页打开。

正确打开方式有两种：

1. 直接打开在线配置生成器：

   [打开配置生成器](https://raw.githack.com/shenyibo666/mimotion/master/config-generator.html)

2. 把 `config-generator.html` 下载到电脑，然后双击打开。

推荐先用第一种。打开后你会看到一个表单页面，不需要看代码。

## 现在的使用方式

这个版本把新手配置尽量做简单了：

- 不再需要配置 `PAT`。
- 不需要手写 JSON 也能用。
- 可以用网页配置生成器帮你生成要填的内容。
- 手动运行时可以选择 `check_config`、`dry_run`、`run`。
- 定时任务会先随机等待一段时间，不再靠修改 workflow 来随机分钟数。

## 它是怎么运行的

```text
GitHub Actions 定时触发
-> GitHub 启动临时 Ubuntu 环境
-> 拉取你的仓库代码
-> 安装 Python 依赖
-> 读取你填在 GitHub Secrets / Variables 里的配置
-> 登录 Zepp Life / 小米运动
-> 计算本次步数
-> 提交步数
-> 保存加密 token，方便下次少登录一次
```

GitHub Actions 不是一台一直在线的服务器。它更像 GitHub 临时借给你的云电脑，用完就关。

## 功能

- 支持邮箱账号和中国手机号账号。
- 支持单账号新手配置。
- 支持高级 `CONFIG` JSON 配置。
- 支持多账号。
- 支持随机步数和固定步数。
- 支持试运行，不真正提交步数。
- 支持 GitHub Actions 定时运行和手动运行。
- 支持 PushPlus 推送。
- 支持本地配置检查。
- 支持网页端配置生成器。

## 最快使用路径

第一次用可以按这个顺序来：

1. Fork 仓库。
2. 打开上面的“配置生成器”，填账号和步数范围。
3. 把生成的内容填到 GitHub 的 Secrets / Variables。
4. 打开 Actions，运行 `MiMotion`，模式选 `check_config`。
5. 再运行一次，模式选 `dry_run`。
6. 确认没问题后，模式选 `run` 正式执行。
7. 以后定时任务会自动运行。

下面是完整教程。

## 第一步：Fork 仓库

打开项目页面，点击右上角 `Fork`，把仓库复制到你自己的 GitHub 账号下。

之后的所有设置，都在你 Fork 后的仓库里做。

## 第二步：打开网页配置生成器

项目里有一个文件：

```text
config-generator.html
```

不要在 GitHub 里直接点文件名看，那样看到的是源码。

推荐直接打开这个链接：

[打开配置生成器](https://raw.githack.com/shenyibo666/mimotion/master/config-generator.html)

也可以把 `config-generator.html` 下载到电脑，再双击打开。

这个页面只在你的浏览器里运行，不会上传账号密码。

它会生成两类内容：

- `Secrets`：适合放账号、密码、AES_KEY、PushPlus token。
- `Variables`：适合放步数范围、运行模式、间隔时间等普通配置。

页面里也可以生成 `CONFIG` JSON。新手不用管这个，直接用 Secrets / Variables 就行。

在配置生成器里，你只需要做三件事：

1. 左边填 Zepp Life 账号、密码、步数范围。
2. 点 `生成配置`。
3. 右边复制 Secrets / Variables 到 GitHub。

## 第三步：配置 GitHub Secrets

进入你 Fork 后的仓库：

```text
Settings -> Secrets and variables -> Actions -> Repository secrets
```

新手模式至少需要填这三个：

| 名称 | 说明 |
| --- | --- |
| `ZEPP_USER` | Zepp Life / 小米运动账号 |
| `ZEPP_PASSWORD` | Zepp Life / 小米运动密码 |
| `AES_KEY` | 16 字节密钥，用于加密保存 token |

如果要 PushPlus 推送，再加：

| 名称 | 说明 |
| --- | --- |
| `PUSH_PLUS_TOKEN` | PushPlus token |

PushPlus 只是“运行结果通知”，不是微信步数同步。不配置它也能刷步数。新手可以先留空，等脚本能正常运行后再考虑是否需要微信通知。

`AES_KEY` 可以用配置生成器生成，也可以自己写 16 位字符串，例如：

```text
1234567890abcdef
```

不要用中文。

## 第四步：配置 GitHub Variables

进入：

```text
Settings -> Secrets and variables -> Actions -> Variables
```

建议新手填这些：

| 名称 | 推荐值 | 说明 |
| --- | --- | --- |
| `MIN_STEP` | `18000` | 随机模式最小步数 |
| `MAX_STEP` | `25000` | 随机模式最大步数 |
| `STEP_MODE` | `random` | `random` 或 `fixed` |
| `FIXED_STEP` | 留空 | 固定模式才需要 |
| `SLEEP_GAP` | `5` | 多账号间隔秒数 |
| `USE_CONCURRENT` | `False` | 是否并发执行 |
| `DRY_RUN` | `True` | 第一次建议先试运行 |
| `RANDOM_DELAY_MINUTES` | `50` | 定时运行前随机等待 0 到 50 分钟 |

如果你只想每天固定刷到 20000 步，可以这样填：

```text
STEP_MODE=fixed
FIXED_STEP=20000
```

如果不填 Variables，脚本也有默认值。但第一次用，建议照着配置生成器填一遍，更清楚。

## 第五步：启用并手动运行 Actions

进入仓库 `Actions` 页面。如果 GitHub 提示 workflow 未启用，点击确认启用。

选择 `MiMotion`，点击 `Run workflow`。

手动运行时有三个模式：

| 模式 | 作用 |
| --- | --- |
| `check_config` | 只检查配置，不登录、不提交步数 |
| `dry_run` | 登录并计算步数，但不提交步数 |
| `run` | 正式运行，会提交步数 |

建议顺序：

1. 先跑 `check_config`。
2. 成功后跑 `dry_run`。
3. 再跑 `run`。

如果你没找到按钮，按这个顺序点：

1. 打开你的 GitHub 仓库。
2. 点顶部的 `Actions`。
3. 左侧点 `MiMotion`。
4. 右侧点 `Run workflow`。
5. 在 `mode` 下拉框里选一个模式。
6. 再点绿色的 `Run workflow`。

运行后页面会出现一条新的记录。点进去，再点 `build`，就能看到日志。

如果 `dry_run` 日志里看到：

```text
DRY_RUN 已开启：会验证登录并计算步数，但不会提交步数
执行账号总数：1，成功：1，失败：0
```

说明基本配置没问题。

正式运行成功后，可以把 Variable 里的 `DRY_RUN` 改成 `False`，让定时任务以后正常提交。

## 如何停止运行

有三种停止方式，按需要选一种。

### 停止正在运行的一次任务

如果 Actions 正在跑，想马上停掉：

1. 进入仓库 `Actions`。
2. 点正在运行的那条记录。
3. 右上角点 `Cancel workflow`。
4. 确认取消。

### 暂时不刷步数，但保留定时任务

把 Variable 里的：

```text
DRY_RUN=False
```

改成：

```text
DRY_RUN=True
```

这样以后定时任务还会运行，但只检查登录和计算步数，不会提交步数。

### 完全停止自动运行

进入仓库：

```text
Actions -> MiMotion -> 右上角 ... -> Disable workflow
```

禁用后，定时任务不会再自动运行。以后想恢复，再点 `Enable workflow`。

## 默认每天几点运行

默认定时配置在：

```text
.github/workflows/run.yml
```

当前 cron 是：

```yaml
cron: '25 1,7,10,12,14,23 * * *'
```

GitHub Actions 用 UTC 时间。换算成北京时间大约是：

```text
09:25
15:25
18:25
20:25
22:25
07:25
```

每次定时触发后，workflow 会再随机等待一段时间。默认等待范围是 0 到 50 分钟，由 `RANDOM_DELAY_MINUTES` 控制。

这样不需要修改 workflow 文件，也不用配置 PAT。

## 步数模式

### random：随机模式

默认模式：

```text
STEP_MODE=random
MIN_STEP=18000
MAX_STEP=25000
```

脚本会根据北京时间缩放步数范围。越接近 22:00，随机范围越接近完整的 `MIN_STEP` 到 `MAX_STEP`。

这样做是为了让步数看起来像一天里慢慢增长，而不是早上突然跳到很高。

### fixed：固定模式

固定模式适合测试，或者你希望每次提交固定步数：

```text
STEP_MODE=fixed
FIXED_STEP=20000
```

固定模式下，`MIN_STEP` 和 `MAX_STEP` 不参与本次计算。

## 高级配置：CONFIG

如果你想配置多账号，或者更喜欢用 JSON，可以继续使用 `CONFIG`。

进入：

```text
Settings -> Secrets and variables -> Actions -> Repository secrets
```

添加 Secret：

```text
CONFIG
```

示例：

```json
{
  "USER": "user1@example.com#user2@example.com",
  "PWD": "password1#password2",
  "MIN_STEP": "18000",
  "MAX_STEP": "25000",
  "STEP_MODE": "random",
  "PUSH_PLUS_TOKEN": "",
  "PUSH_PLUS_HOUR": "",
  "PUSH_PLUS_MAX": "30",
  "SLEEP_GAP": "8",
  "USE_CONCURRENT": "False",
  "DRY_RUN": "True"
}
```

如果同时配置了 `CONFIG` 和新手模式的 `ZEPP_USER` / `ZEPP_PASSWORD`，脚本会优先使用 `CONFIG`。

多账号时，账号和密码都用 `#` 分隔，并且数量必须一致。

## 本地调试

本地调试不是必须的。它适合你想先在电脑上检查配置。

安装依赖：

```bash
pip install -r requirements.txt
```

复制配置模板：

```bash
cp config.local.example.json config.local.json
```

Windows PowerShell：

```powershell
Copy-Item config.local.example.json config.local.json
```

检查配置：

```bash
python main.py --check-config
```

试运行：

```bash
python main.py --dry-run
```

`config.local.json` 已经写在 `.gitignore` 里，不会被提交。

## 安全说明

新手模式并不会让邮箱更容易泄露。关键是这几条：

- 真实账号密码只放 GitHub Secrets。
- 不要把真实账号密码写进 `README.md`、`main.py` 或其他仓库文件。
- 不要提交 `config.local.json`。
- 日志只会显示脱敏账号。
- 现在不再需要配置高权限 `PAT`。

`config-generator.html` 也不会把账号密码发到服务器。它只是一个本地网页，负责帮你生成要复制的内容。

## 常见问题

### PushPlus 是什么？必须配置吗？

不是必须。

PushPlus 是微信通知工具。配置它以后，脚本运行成功或失败时，可以给你推送一条微信通知。

它和“微信运动步数同步”不是一回事：

- 微信运动步数同步：Zepp Life 把步数同步给微信运动。
- PushPlus 推送：脚本把运行结果通知你。

新手可以先不配置 `PUSH_PLUS_TOKEN`。

### Actions 成功了，但微信步数没变？

这个项目不直接修改微信。它提交的是 Zepp Life / 小米运动数据。微信是否更新，取决于第三方同步。

可以先看 Zepp Life 里步数有没有变化，再检查微信运动绑定状态。

### 第一次运行提示 token 解密失败？

通常是仓库里的 `encrypted_tokens.data` 不是用你的 `AES_KEY` 生成的。第一次遇到可以忽略，成功登录后会重新生成。

### 出现 429 怎么办？

429 一般是请求太频繁。可以这样处理：

- 关闭 `USE_CONCURRENT`。
- 增大 `SLEEP_GAP`。
- 减少账号数量。
- 等一段时间再手动运行。

### 为什么不再需要 PAT？

旧版本通过修改 workflow 文件来随机下一次运行时间，所以需要 PAT。

现在改成了“定时触发后随机等待”，不再修改 workflow 文件。保存 `encrypted_tokens.data` 使用 GitHub 自带的 `GITHUB_TOKEN` 就够了。

### 怎么确认本次用了多少步？

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
| `main.py` | 主入口，读取配置、执行账号任务、推送结果 |
| `config-generator.html` | 网页端配置生成器 |
| `config.local.example.json` | 本地调试配置模板 |
| `requirements.txt` | Python 依赖列表 |
| `util/zepp_helper.py` | Zepp/华米接口请求逻辑 |
| `util/aes_help.py` | AES 加密和解密 |
| `.github/workflows/run.yml` | GitHub Actions 主任务 |
| `encrypted_tokens.data` | 加密后的 token 缓存 |

## 参考与致谢

这个项目是在前人工作的基础上继续整理和维护的。感谢这些项目和作者提供的接口思路、参数样例和加密方式参考：

- [TonyJiangWJ/mimotion](https://github.com/TonyJiangWJ/mimotion)
- [huangshihai/mimotion](https://github.com/huangshihai/mimotion)
- 已不可访问的 `xunichanghuan/mimotion`
- [hanximeng/Zepp_API](https://github.com/hanximeng/Zepp_API)

如果这些项目对你有帮助，也可以去原项目看看。很多小工具能继续用下去，就是靠后来的人一点点接着维护。
