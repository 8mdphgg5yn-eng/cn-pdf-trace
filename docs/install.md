# 安装与从零复现

本说明对应v0.2.1试用版，不是旧v0.2.0的安装说明。版本变化见[更新说明](../CHANGELOG.md)。完整演示要求macOS、已有Python 3.12、uv、curl及可用的Vision框架。本机验证组合为macOS 27.0.1 arm64、Python 3.12.14、uv 0.11.7。不是跨系统安装保证。

尚未安装前置工具时，可按 [Python官方入口](https://www.python.org/downloads/) 和 [uv官方安装说明](https://docs.astral.sh/uv/getting-started/installation/)自行选择安装方式。本项目不修改系统Python、不安装系统级工具。原生PDF功能理论上可在其他系统运行，但Linux、Windows及Intel Mac未作本轮从零实测；完整回归需要macOS OCR，不能通过跳过扫描测试冒充通过。

本地CPU方案在Linux上将torch 2.14.1及torchvision 0.29.1锁到官方CPU索引（构建后缀为+cpu），其他包仍来自PyPI，macOS沿用PyPI构建。应保留pyproject.toml与uv.lock并按下述uv命令安装；这里使用explicit索引，只为这两个包指定来源。更新后的锁不含NCCL、NVSHMEM、CUDA/NVIDIA包或triton，原版条件依赖的许可问题作为历史事实保留在 [第三方说明](../third_party/NOTICE.md)。

此配置由uv读取，不会随wheel的标准Requires-Dist字段传递给普通pip。直接`pip install`、传入`--no-sources`、更换或重建锁文件，可能再次选到Linux CUDA构建；不能把CPU运行设置当成依赖排除。不要用`--no-deps`或卸载NCCL/NVSHMEM来破坏CUDA版torch的声明依赖。本版仍只实际运行于macOS；Linux x86_64与aarch64仅核对依赖解析及安装计划，未在Linux执行PDF转换或OCR。仍不提供捆绑第三方二进制的离线包或容器。

## 普通安装

从[v0.2.1 Release](https://github.com/8mdphgg5yn-eng/cn-pdf-trace/releases/tag/v0.2.1)下载`cn_pdf_trace-0.2.1.tar.gz`，或使用对应v0.2.1标签的完整源码。不要通过旧v0.2.0复现这里的CPU依赖排除。下载页提供SHA256SUMS.txt，可运行`shasum -a 256 cn_pdf_trace-0.2.1.tar.gz`并与其中对应行比较。下载齐校验和列出的全部附件时，也可运行`shasum -a 256 -c SHA256SUMS.txt`检查全部文件；哈希只核对字节一致性，不证明司法真实性。

源码包安装先执行下面两行，把第一行引号中的路径换成实际收到的包路径；在新的工作目录解压，不覆盖已有源码或输出。wheel不含测试样本、安装脚本和冻结锁，不能代替完整源码包。

```sh
tar -xzf "/本地包目录/cn_pdf_trace-0.2.1.tar.gz"
cd cn_pdf_trace-0.2.1
```

确认存在pyproject.toml、uv.lock、models.lock.json和font.lock.json，并确认pyproject.toml含pytorch-cpu显式索引、torch及torchvision的Linux来源配置。只复制wheel、只复制uv.lock或沿用旧版pyproject.toml都不属于这里核对过的安装方式。本版以源码安装，不需要PyPI账号或收费API。

```sh
uv --version
curl --version
python3.12 --version

uv --native-tls sync --python python3.12 --no-python-downloads \
  --frozen --no-editable --extra dev --extra ocr-mac

.venv/bin/python -c 'import cntrace; from importlib.metadata import version; assert cntrace.__version__ == version("cn-pdf-trace") == "0.2.1"; print("cn-pdf-trace", cntrace.__version__)'
```

若解释器不叫python3.12，将 `--python` 后的值替换为已有Python 3.12的路径。`--no-python-downloads` 避免安装时悄悄下载另一个解释器。`--no-editable` 使后续命令使用已安装的本项目wheel；本机曾遇到隐藏的editable .pth未被加载的问题，原因未完全确认。

只转换原生PDF可省略 `--extra ocr-mac`；这不代表能够运行包含扫描件的完整测试。`dev` 依赖用于制作自制样本和回归，普通转换的安装可以省略，但此时不能按下面步骤重新生成样本或执行测试。

修改src代码后重新安装，而不是只编辑文件后沿用旧wheel：

```sh
uv --native-tls sync --frozen --no-editable --extra dev --extra ocr-mac \
  --reinstall-package cn-pdf-trace
```

## 下载公开资源与生成样本

下载前请阅读 [第三方说明](../third_party/NOTICE.md)及其中的固定版本模型卡、字体许可来源。Heron布局模型的固定模型卡标记Apache-2.0，TableFormer所在模型仓库的固定模型卡标记CDLA-Permissive-2.0，Noto Sans SC字体采用SIL OFL 1.1；它们不适用本项目MIT。相关原文见 [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0)、[CDLA-Permissive-2.0](https://cdla.dev/permissive-2-0/)及源码third_party/NotoSansSC-OFL.txt。运行脚本由你决定，本项目不代你接受第三方条款。下载供本地使用与将权重或字体另行打包发布，应分别核对适用条件。

依赖已由上面的安装命令取得；此步骤需要联网，下载两个固定公开模型和开放字体，不调用收费API。不要向下载脚本传入文档或密钥。模型约367 MiB，字体原始文件约17 MiB，安装环境约1.2 GiB；干净验证还会保留独立uv缓存，建议预留数GiB空间。大小是当前配置的目录统计，不是最低硬件要求。

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
  .venv/bin/python -m pytest -c pyproject.toml --rootdir=. --confcutdir=. \
  -q --junitxml=output/regression.xml

.venv/bin/python scripts/acceptance.py \
  --junit output/regression.xml --out output/acceptance.json
```

run_demo依次处理10份自制样本，创建10个输出目录。pytest会再转换每份样本两次；测试通过包含“正确报告不支持、待核对和失配”，不等于100条摘录都成功。具体计数看acceptance.json。

单份转换或查询遇到OCR待核对、歧义或失配时，CLI退出1；文件仍可已生成。不要在这些命令后机械地套 `set -e` 并把退出1解释成安装失败。见 [使用示例](usage.md)。

## 完整的干净验证

下面命令仅在新的目标目录执行。目标已存在即拒绝，不删除或复用旧环境。调用它的解释器只用于启动编排；实际项目另建虚拟环境并重新下载依赖。不需要旧output基线或上游贡献草稿；使用本完整源码副本即可启动，不依赖未随源码提供的项目文件。

```sh
.venv/bin/python scripts/reproduce_clean.py \
  --python /已有Python3.12的路径/python3 \
  --dest tmp/clean-check-new
```

不写 `--python` 时使用启动解释器的base_prefix下的python3，不应假定每台机器都采用相同路径。需在运行前确认它存在且为3.12。

脚本复制源码、锁文件、更新说明、随包examples及第三方许可，不复制旧.venv、依赖缓存、模型、fixtures或output，也不复制上游审阅记录。examples仅供查看；本次演示和测试基线由脚本在新output目录中重新生成。它创建空的uv缓存，禁用用户site-packages与旧PYTHONPATH，先验证cntrace确实从新.venv导入，再下载模型和字体并生成所有PDF。安装与下载联网；生成、转换、回归及验收使用系统禁止联网沙箱。

结果留在目标目录的result.json和logs中；project包含复现现场。脚本生成两次，要求10份PDF及gold.json逐字节相同，随后完成三类输出、64项回归及验收。不会为满足复现而删除既有目录或放宽失败状态。具体核验范围见 [测试说明](testing.md)。

## 常见情况

| 现象 | 处理 |
| --- | --- |
| ModuleNotFoundError: cntrace | 确认在根目录且用.venv解释器；按上文重装非editable wheel。不要改系统导入路径。 |
| 缺少模型或哈希不同 | 先运行公开资源准备并核对具体文件；不要让转换器临时上网兜底。 |
| OCR包或Vision不可用 | 检查macOS及ocr-mac extra；可显式关闭OCR，但不能把扫描演示记为通过。 |
| 扫描页缺少候选或回归结果前后不同 | 本轮曾捕获Vision计算后端错误，首次空缓存回归未通过、同环境重试通过，根因仍待核。保留result.json及日志，完整验收按失败处理；不要降低阈值、跳过扫描测试或用旧输出替换结果。见测试说明。 |
| 找不到output/regression.xml | 先完成演示和pytest，再给acceptance传入实际JUnit路径。 |
| CLI退出1 | 检查JSON或报告，是歧义、待核对、未定位或一致性问题；不是统一的程序崩溃。 |
| TLS或下载失败 | 检查本机信任与网络，uv使用native-tls、curl保留验证；不使用-k。 |
| 重新安装后行为没变化 | 核对.venv/bin/python及cntrace.__file__，确认测试的安装副本；源代码修改后必须重建安装。 |

uv.lock固定运行依赖与平台条件，但不固定整个macOS、系统OCR模型、基础解释器或网络资源可用性。build-system的hatchling仍采用pyproject中的允许范围，本轮不是完整可重现构建或离线安装发行包。
