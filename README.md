# mimotion

mimotion 是一个用 GitHub Actions 自动运行的 Zepp Life / 小米运动步数同步脚本。

它不会直接修改微信数据。脚本做的是：登录你的 Zepp Life / 小米运动账号，把当天步数提交到 Zepp/华米接口。如果你的 Zepp Life 已经绑定了微信运动、支付宝运动等平台，后续这些平台可能会同步到新的步数。

你不需要买服务器，也不需要电脑每天开着。GitHub Actions 到点后会临时启动一台运行环境，执行仓库里的脚本，执行完就结束。

> 请只操作你自己的账号。账号、密码、AES_KEY 都是敏感信息，不要写进公开代码，不要发到截图、issue 或日志里。

## 一句话流程

新手按这个顺序做：

1. Fork 仓库。
2. 打开配置生成器。
3. 把配置生成器里的内容，一个一个填到 GitHub Secrets / Variables。
4. 去 Actions 手动运行 `check_config`。
5. 再运行 `dry_run`。
6. 没问题后运行 `run`。
7. 最后把 `DRY_RUN` 改成 `False`，以后就会定时自动运行。

## 不要直接点开 HTML 文件

如果你在 GitHub 里点击 `config-generator.html`，看到满屏代码，这是正常的。GitHub 是在给你看源码，不是在打开网页。

请用下面这个链接打开配置生成器：

[打开配置生成器](https://raw.githack.com/shenyibo666/mimotion/master/config-generator.html)

打开后应该看到表单页面。如果还是看到代码，就换一种方式：把 `config-generator.html` 下载到电脑，然后双击打开。

配置生成器不会上传你的账号密码。它只在浏览器里帮你生成要复制的内容。

## 先弄清楚两个 GitHub 页面

后面会用到两个设置页面：

### Secrets 页面

位置：

```text
仓库 -> Settings -> Secrets and variables -> Actions -> Secrets
```

Secrets 用来放敏感信息，比如账号、密码、AES_KEY。

添加方法：

1. 点 `New repository secret`。
2. `Name` 填变量名，比如 `ZEPP_USER`。
3. `Secret` 填变量值，比如你的 Zepp Life 账号。
4. 点 `Add secret`。

### Variables 页面

位置：

```text
仓库 -> Settings -> Secrets and variables -> Actions -> Variables
```

Variables 用来放普通配置，比如步数范围、是否试运行。

添加方法：

1. 点 `New repository variable`。
2. `Name` 填变量名，比如 `MIN_STEP`。
3. `Value` 填变量值，比如 `18000`。
4. 点 `Add variable`。

简单说：

- Secrets 填账号密码这类不能公开的东西。
- Variables 填步数、模式、开关这类普通配置。

## 第一步：Fork 仓库

打开项目页面，点右上角 `Fork`。

Fork 完成后，后面的设置都在你自己的仓库里做，不是在原仓库里做。

## 第二步：使用配置生成器

打开：

[配置生成器](https://raw.githack.com/shenyibo666/mimotion/master/config-generator.html)

在左边填写：

- Zepp Life 账号
- Zepp Life 密码
- 最小步数
- 最大步数
- 步数模式
- 你的仓库地址

第一次建议：

```text
最小步数：18000
最大步数：25000
步数模式：random
第一次先试运行：勾选
多账号并发执行：不勾选
PushPlus Token：留空
```

然后点：

```text
生成配置
```

右边会出现两张表：

- 新手模式：Secrets
- 新手模式：Variables

接下来就是把这两张表里的内容填到 GitHub。

## 第三步：填写 Secrets

进入你自己的仓库：

```text
Settings -> Secrets and variables -> Actions -> Secrets
```

至少添加下面三个 Secret。

### 1. ZEPP_USER

点 `New repository secret`。

```text
Name: ZEPP_USER
Secret: 你的 Zepp Life / 小米运动账号
```

然后点 `Add secret`。

### 2. ZEPP_PASSWORD

再点一次 `New repository secret`。

```text
Name: ZEPP_PASSWORD
Secret: 你的 Zepp Life / 小米运动密码
```

然后点 `Add secret`。

### 3. AES_KEY

再点一次 `New repository secret`。

```text
Name: AES_KEY
Secret: 配置生成器生成的 AES_KEY
```

然后点 `Add secret`。

`AES_KEY` 是用来加密保存登录 token 的。它必须是 16 位字符串。配置生成器会帮你生成。

### 4. PUSH_PLUS_TOKEN，可选

这个可以先不填。

PushPlus 只是微信通知工具，用来通知你脚本运行成功或失败。它不是微信步数同步。不配置它也能刷步数。

如果以后想要运行结果通知，再添加：

```text
Name: PUSH_PLUS_TOKEN
Secret: 你的 PushPlus token
```

## 第四步：填写 Variables

进入你自己的仓库：

```text
Settings -> Secrets and variables -> Actions -> Variables
```

点 `New repository variable`，逐个添加下面这些。

| Name | Value | 为什么需要 |
| --- | --- | --- |
| `MIN_STEP` | `18000` | 随机模式的最小步数 |
| `MAX_STEP` | `25000` | 随机模式的最大步数 |
| `STEP_MODE` | `random` | 步数模式，先用随机模式 |
| `SLEEP_GAP` | `5` | 多账号时每个账号之间间隔几秒 |
| `USE_CONCURRENT` | `False` | 是否并发执行，新手先关掉 |
| `DRY_RUN` | `True` | 第一次先试运行，不真正提交步数 |
| `RANDOM_DELAY_MINUTES` | `50` | 定时运行前随机等待 0 到 50 分钟 |

`FIXED_STEP` 可以先不填。只有固定步数模式才需要它。

如果你以后想固定每天刷 20000 步，改成：

```text
STEP_MODE=fixed
FIXED_STEP=20000
```

## 第五步：手动运行 Actions

进入你的仓库，点顶部的：

```text
Actions
```

如果 GitHub 提示 workflow 未启用，点确认启用。

然后按这个顺序点：

1. 左侧点 `MiMotion`。
2. 右侧点 `Run workflow`。
3. 会出现一个 `mode` 下拉框。
4. 先选择 `check_config`。
5. 点绿色的 `Run workflow`。

三个模式的意思：

| mode | 作用 |
| --- | --- |
| `check_config` | 只检查配置，不登录、不刷步数 |
| `dry_run` | 登录并计算步数，但不真正提交 |
| `run` | 正式运行，会提交步数 |

推荐运行顺序：

1. 先运行 `check_config`。
2. 成功后运行 `dry_run`。
3. 再运行 `run`。

## 第六步：查看日志

运行后，Actions 页面会出现一条新的记录。

查看方法：

1. 点那条新的运行记录。
2. 点 `build`。
3. 找到 `Run MiMotion`。
4. 展开后看日志。

如果 `check_config` 成功，会看到：

```text
配置检查通过
```

如果 `dry_run` 成功，会看到类似：

```text
DRY_RUN 已开启：会验证登录并计算步数，但不会提交步数
执行账号总数：1，成功：1，失败：0
```

如果 `run` 成功，会看到本次步数和成功数量。

## 第七步：正式开启定时刷步

确认 `run` 成功后，回到 Variables 页面，把：

```text
DRY_RUN=True
```

改成：

```text
DRY_RUN=False
```

这样以后定时任务就会正式提交步数。

默认大约每天这些北京时间运行：

```text
07:25
09:25
15:25
18:25
20:25
22:25
```

每次触发后还会随机等待 0 到 50 分钟，所以实际时间会稍微后移。

## 如何停止

### 停止正在运行的一次任务

1. 进入 `Actions`。
2. 点正在运行的那条记录。
3. 右上角点 `Cancel workflow`。
4. 确认取消。

### 暂时不刷，但保留定时任务

把 Variables 里的：

```text
DRY_RUN=False
```

改成：

```text
DRY_RUN=True
```

这样以后还是会定时运行，但不会真正提交步数。

### 完全停止自动运行

进入：

```text
Actions -> MiMotion
```

点右上角的 `...`，选择：

```text
Disable workflow
```

以后想恢复，再点 `Enable workflow`。

## 之前的日志怎么清除

日志就是 Actions 里的运行记录。它不影响后续使用，不清理也没关系。

如果你想删除某一条记录：

1. 进入 `Actions`。
2. 点一条历史运行记录。
3. 右上角点 `...`。
4. 选择 `Delete workflow run`。

GitHub 没有很方便的一键清空按钮，一般不用专门清理。

## 多个账号怎么同时刷

新手模式也支持多账号。

在 Secrets 里这样填：

```text
ZEPP_USER=账号1#账号2#账号3
ZEPP_PASSWORD=密码1#密码2#密码3
```

注意三点：

1. 账号之间用英文 `#` 分隔。
2. 密码之间也用英文 `#` 分隔。
3. 账号和密码数量必须一样，顺序也要对应。

例子：

```text
ZEPP_USER=a@example.com#b@example.com
ZEPP_PASSWORD=aaa111#bbb222
```

表示：

```text
a@example.com 使用 aaa111
b@example.com 使用 bbb222
```

多账号建议先保持：

```text
USE_CONCURRENT=False
SLEEP_GAP=8
```

这样会一个账号一个账号执行，更稳一点。

如果账号很多，想同时执行，可以改成：

```text
USE_CONCURRENT=True
```

但并发更容易触发接口限制。新手不建议一开始就开。

## PushPlus 和微信步数不是一回事

这里很容易混。

微信步数同步：

```text
Zepp Life / 小米运动 -> 微信运动
```

这是第三方平台同步，本项目不能直接控制。

PushPlus 推送：

```text
脚本运行结果 -> 微信通知
```

它只是通知你“成功了”或“失败了”。不配置 PushPlus，不影响刷步数。

所以第一次使用时，`PUSH_PLUS_TOKEN` 可以留空。

## 步数模式

### random：随机模式

推荐新手先用：

```text
STEP_MODE=random
MIN_STEP=18000
MAX_STEP=25000
```

脚本会根据北京时间缩放步数范围。越接近 22:00，随机范围越接近完整的 `MIN_STEP` 到 `MAX_STEP`。

### fixed：固定模式

如果你想每天固定刷到 20000 步：

```text
STEP_MODE=fixed
FIXED_STEP=20000
```

固定模式下，`MIN_STEP` 和 `MAX_STEP` 不参与计算。

## 高级配置：CONFIG

新手不用看这一节。

如果你熟悉 JSON，可以只配置一个 Secret：

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

## 本地调试，可选

不懂命令行可以跳过这一节。

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

## 常见问题

### Actions 成功了，但微信步数没变？

这个项目不直接修改微信。它提交的是 Zepp Life / 小米运动数据。微信是否更新，取决于第三方同步。

先看 Zepp Life 里步数有没有变化，再检查微信运动绑定状态。

### 第一次运行提示 token 解密失败？

通常是仓库里的 `encrypted_tokens.data` 不是用你的 `AES_KEY` 生成的。第一次遇到可以忽略，成功登录后会重新生成。

### 出现 429 怎么办？

429 一般是请求太频繁。可以这样处理：

- 关闭 `USE_CONCURRENT`。
- 增大 `SLEEP_GAP`。
- 减少账号数量。
- 等一段时间再手动运行。

### 为什么不需要 PAT？

旧版本通过修改 workflow 文件来随机下一次运行时间，所以需要 PAT。

现在改成了“定时触发后随机等待”，不再修改 workflow 文件。保存 `encrypted_tokens.data` 使用 GitHub 自带的 `GITHUB_TOKEN` 就够了。

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
