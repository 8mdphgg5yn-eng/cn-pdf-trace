# 安装与从零复现

本说明对应0.2.0。完整演示要求macOS、已有Python 3.12、uv、curl及可用的Vision框架。本机验证组合为macOS 27.0.1 arm64、Python 3.12.14、uv 0.11.7。不是跨系统安装保证。

尚未安装前置工具时，可按 [Python官方入口](https://www.python.org/downloads/) 和 [uv官方安装说明](https://docs.astral.sh/uv/getting-started/installation/)自行选择安装方式。本项目不修改系统Python、不安装系统级工具。原生PDF功能理论上可在其他系统运行，但Linux、Windows及Intel Mac未作本轮从零实测；完整回归需要macOS OCR，不能通过跳过扫描测试冒充通过。

## 普通安装

下载本仓库源码ZIP并解压后进入根目录，或执行以下命令：

```sh
git clone https://github.com/8mdphgg5yn-eng/cn-pdf-trace.git
cd cn-pdf-trace
```

确认存在pyproject.toml、uv.lock、models.lock.json和font.lock.json。本版以源码安装，不需要PyPI账号或收费API。

```sh
uv --version
curl --version
python3.12 --version

uv --native-tls sync --python python3.12 --no-python-downloads \
  --frozen --no-editable --extra dev --extra ocr-mac
```

若解释器不叫python3.12，将 `--python` 后的值替换为已有Python 3.12的路径。`--no-python-downloads` 避免安装时悄悄下载另一个解释器。`--no-editable` 使后续命令使用已安装的本项目wheel；本机曾遇到隐藏的editable .pth未被加载的问题，原因未完全确认。

只转换原生PDF可省略 `--extra ocr-mac`；这不代表能够运行包含扫描件的完整测试。`dev` 依赖用于制作自制样本和回归，普通转换的安装可以省略，但此时不能按下面步骤重新生成样本或执行测试。

修改src代码后重新安装，而不是只编辑文件后沿用旧wheel：

```sh
uv --native-tls sync --frozen --no-editable --extra dev --extra ocr-mac \
  --reinstall-package cn-pdf-trace
```

## 下载公开资源与生成样本

此步骤需要联网，只下载免费依赖、两个固定公开模型和开放字体。不要向下载脚本传入文档或密钥。模型约367 MiB，字体原始文件约17 MiB，安装环境约1.2 GiB；干净验证还会保留独立uv缓存，建议预留数GiB空间。大小是当前配置的目录统计，不是最低硬件要求。

```sh
.venv/bin/python scripts/prepare_assets.py
.venv/bin/python scripts/make_fixtures.py
```

prepare_assets校验模型和字体哈希，不能因为不匹配就更新锁文件使它通过。下载中断留下的.part可以在下一次下载时覆盖；已完成但损坏的单个缓存文件需核实后移走再重下载。不要删除整个源码、客户文件或模型锁文件，不要关闭TLS证书验证。

## 离线演示与完整回归

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 \
  /usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  .venv/bin/python scripts/run_demo.py

HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 \
  /usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  .venv/bin/python -m pytest -q --junitxml=output/regression.xml

.venv/bin/python scripts/acceptance.py \
  --junit output/regression.xml --out output/acceptance.json
```

run_demo依次处理10份自制样本，创建10个输出目录。pytest会再转换每份样本两次；测试通过包含“正确报告不支持、待核对和失配”，不等于100条摘录都成功。具体计数看acceptance.json。

单份转换或查询遇到OCR待核对、歧义或失配时，CLI退出1；文件仍可已生成。不要在这些命令后机械地套 `set -e` 并把退出1解释成安装失败。见 [使用示例](usage.md)。

## 完整的干净验证

下面命令仅在新的目标目录执行。目标已存在即拒绝，不删除或复用旧环境。调用它的解释器只用于启动编排；实际项目另建虚拟环境并重新下载依赖。不需要旧output基线或上游贡献草稿；从公开源码即可运行。

```sh
.venv/bin/python scripts/reproduce_clean.py \
  --python /已有Python3.12的路径/python3 \
  --dest tmp/clean-check-new
```

不写 `--python` 时使用启动解释器的base_prefix下的python3，不应假定每台机器都采用相同路径。需在运行前确认它存在且为3.12。

脚本仅复制源码、锁文件、说明及第三方许可，不复制旧.venv、依赖缓存、模型、fixtures或output，也不复制上游审阅记录。它创建空的uv缓存，禁用用户site-packages与旧PYTHONPATH，先验证cntrace确实从新.venv导入，再下载模型和字体并生成所有PDF。安装与下载联网；生成、转换、回归及验收使用系统禁止联网沙箱。

结果留在目标目录的result.json和logs中；project包含复现现场。脚本生成两次，要求10份PDF及gold.json逐字节相同，随后完成三类输出、64项回归及验收。不会为满足复现而删除既有目录或放宽失败状态。具体核验范围见 [测试说明](testing.md)。

## 常见情况

| 现象 | 处理 |
| --- | --- |
| ModuleNotFoundError: cntrace | 确认在根目录且用.venv解释器；按上文重装非editable wheel。不要改系统导入路径。 |
| 缺少模型或哈希不同 | 先运行公开资源准备并核对具体文件；不要让转换器临时上网兜底。 |
| OCR包或Vision不可用 | 检查macOS及ocr-mac extra；可显式关闭OCR，但不能把扫描演示记为通过。 |
| 找不到output/regression.xml | 先完成演示和pytest，再给acceptance传入实际JUnit路径。 |
| CLI退出1 | 检查JSON或报告，是歧义、待核对、未定位或一致性问题；不是统一的程序崩溃。 |
| TLS或下载失败 | 检查本机信任与网络，uv使用native-tls、curl保留验证；不使用-k。 |
| 重新安装后行为没变化 | 核对.venv/bin/python及cntrace.__file__，确认测试的安装副本；源代码修改后必须重建安装。 |

uv.lock固定运行依赖与平台条件，但不固定整个macOS、系统OCR模型、基础解释器或网络资源可用性。build-system的hatchling仍采用pyproject中的允许范围，本轮不是完整可重现构建或离线安装发行包。
