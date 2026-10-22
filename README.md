# 中文文档原文定位与核对工具

本地命令行工具，版本0.2.1，供试用与复现。以 Docling™ 为解析基础，将 Markdown 摘录与 PDF 的页面、区域和来源文字一起保存，并检查后续变化。现有10份完全自制样本，含债权表、复杂跨页表格、纯扫描件与混合PDF，不代表已验证一般中文案卷。

OCR默认关闭，可显式复用Docling已有的macOS Vision本地接口。OCR文字与位置均为待人工核对候选，不进入已核验计数。不接入聊天、知识库、服务器或收费API。本项目自有代码、文档及自制样本按 [MIT许可证](LICENSE)开源，版权署名Mgb。第三方组件、字体与模型分别适用各自条款，见 [第三方说明](third_party/NOTICE.md)。

Docling™ 是 LF Projects, LLC 的商标。本项目为独立下游工具；对 Docling 的提及仅说明技术依赖，不表示由 Docling 或 LF Projects, LLC 官方维护、认可或认证。相关要求见 [LF Projects 商标政策](https://lfprojects.org/policies/trademark-policy/)。

v0.2.1的变化见[更新说明](CHANGELOG.md)，源码包从[v0.2.1试用版](https://github.com/8mdphgg5yn-eng/cn-pdf-trace/releases/tag/v0.2.1)获取。请使用本版完整源码或`cn_pdf_trace-0.2.1.tar.gz`；旧v0.2.0不包含CPU安装来源等修改。按随源码提供的pyproject.toml和uv.lock执行下述`uv sync --frozen`；此时Linux的torch与torchvision来自官方CPU索引，锁中不含NCCL、NVSHMEM及CUDA/NVIDIA包。直接使用pip安装wheel或忽略uv源配置不能获得同样保证。macOS功能回归与Linux安装计划的实际验证范围见安装说明；不据此宣称整个依赖栈的全部权利已经审清。

本版保留扫描OCR首次空缓存运行不稳定的已知问题：首次回归56项通过、8项失败，同环境重试64项通过。已捕获Apple Vision计算后端错误，底层原因尚未闭合，本版不承诺扫描OCR首次运行稳定。失败现场和重试结果分别记录，不能将重试通过视为首次从零复现通过；详见[测试说明](docs/testing.md)。

无需安装即可先查看自制合同的 [Markdown](examples/contract-output/document.md)、[溯源JSON](examples/contract-output/provenance.json)和[核对报告](examples/contract-output/check-report.md)。

## 自制测试样本

| 自制样本 | PDF | 三类输出目录 |
| --- | --- | --- |
| 采购合同 | `fixtures/contract.pdf` | `output/contract/` |
| 工程结算表 | `fixtures/settlement.pdf` | `output/settlement/` |
| 两页债权表 | `fixtures/creditors.pdf` | `output/creditors/` |
| 合并表头债权表 | `fixtures/creditors_merged.pdf` | `output/creditors_merged/` |
| 三页多行续表 | `fixtures/table_three_pages.pdf` | `output/table_three_pages/` |
| 无重复表头续表 | `fixtures/table_no_header.pdf` | `output/table_no_header/` |
| 三类页码及歧义 | `fixtures/page_labels.pdf` | `output/page_labels/` |
| 清晰扫描合同 | `fixtures/scan_contract.pdf` | `output/scan_contract/` |
| 低清债权表扫描 | `fixtures/scan_degraded.pdf` | `output/scan_degraded/` |
| 原生与扫描混合PDF | `fixtures/hybrid.pdf` | `output/hybrid/` |

每个输出目录只有 `document.md`、`provenance.json`、`check-report.md`。`output/` 不纳入版本控制，按下述步骤生成；仓库中的 `fixtures/` 仅含程序绘制的自制材料。

合同包含无印刷页码的封面、PDF 实际第2页印“第1页”、重复条款和重复金额。结算表包含重复金额、重复表头和一条跨页续行记录；程序保留两页的表格片段，不自动认定续行属于某条记录。

## 安装、使用和复现

按[安装说明](docs/install.md)安装锁定依赖、准备公开模型和字体，再生成样本。完整演示要求已有Python 3.12、uv、curl及macOS Vision。安装和下载联网，转换和回归可在系统禁止联网沙箱中运行。

```sh
uv --native-tls sync --python python3.12 --no-python-downloads \
  --frozen --no-editable --extra dev --extra ocr-mac
.venv/bin/python scripts/prepare_assets.py
.venv/bin/python scripts/make_fixtures.py
.venv/bin/python scripts/run_demo.py
.venv/bin/python -m pytest -c pyproject.toml --rootdir=. --confcutdir=. \
  -q --junitxml=output/regression.xml
.venv/bin/python scripts/acceptance.py --junit output/regression.xml --out output/acceptance.json
```

处理自己的原生文字PDF时，将下列路径换成已经存在的本地文件；扫描件需额外安装ocr-mac并显式加上 `--ocr mac`：

```sh
.venv/bin/cntrace convert "/你的目录/文件.pdf" --out output/my-document
.venv/bin/cntrace verify "/你的目录/文件.pdf" \
  --bundle output/my-document --quote '需要核对的原文摘录'
```

解释器路径、断网命令、资源用量及干净验证步骤见安装说明。本版通过源码安装，不假定已在PyPI提供同名包。修改src后须重建非editable安装，不能继续测试旧wheel。

[使用示例](docs/usage.md)包括转换、唯一摘录、重复金额、不存在的文字、扫描候选以及文件变化核对。CLI退出0表示本次检查通过；退出1表示有失配、歧义、未定位或待核对；退出2表示输入或环境错误。扫描转换通常退出1，但仍保存三类输出。verify默认打印JSON，显式传入--report才另存报告。

[已知限制](docs/limitations.md)说明原生文字核验与肉眼画面的区别、OCR边界、表格展平、编号稳定范围和哈希用途。跨页表格按页保留，不推断续行归属；重复候选全部列出，不能选择第一处。

## 最小数据约定

`provenance.json` 保存文件完整 SHA-256、实际页数、解析器及模型版本、配置指纹、页面信息和摘录记录。

- `pdf_page`：从1开始的实际页面序号。
- `printed_page_label`：从页脚明确的“第…页”文字识别，可能为空。不是根据封面偏移计算。
- `ocr_printed_page_candidates`：扫描页脚识别出的候选，始终另列待核对，不回填为已确认的印刷页码。
- `pdf_page_label`：PDF 内部页标签，只有文件确有对应标签树时才读取，不冒充印刷页码。
- `bbox`：`[left, top, right, bottom]`，左上原点，单位 pt；粒度为文本块或表格单元格。
- `parser_charspan`：解析器原有范围，属于该文档元素，不是 Markdown 范围，也不是单字坐标。
- `markdown_range`：Unicode 码点计数，左闭右开；不等于 UTF-8 字节或 JavaScript UTF-16 单元。
- `sources`：来源片段列表，一段摘录允许对应多个来源区域。
- `id`：限定于同一文件、锁定解析环境、配置和输出的确定性编号；跨版本或改文件不保证不变。
- `source_binding_sha256`：检查来源描述是否意外变化，不提供数字签名或防恶意篡改证明。

`verified`需要两层核对：Markdown可见文字与来源片段一致，来源区域的PDFium原生文字层与片段一致。OCR候选不会通过这项独立文字核验。只有空白被忽略，不替换数字、金额、标点或中文数字。另以原PDF的原生字符位置检查未被任何来源区域覆盖的文字，避免解析器遗漏整段后静默通过。

当前数据格式为schema 2；验证命令仍接受较早的schema 1。旧输出需与其原始PDF一起保存，不保证跨工具版本沿用旧编号。

## 验收依据与后续

`fixtures/gold.json` 来自样本绘制时记录的文字、页序和区域，不来自解析结果。测试同时要求所有成功来源符合正确答案，以及所有预设核对项均被覆盖，避免“全部拒绝所以零错误”。

[回归与从零复现](docs/testing.md)说明测试分母、步骤和核验边界；[样本导航](docs/samples.md)列出10份自制PDF。原生230项绘制检查点在已验证环境中均覆盖，扫描候选34项中29项匹配、5项未匹配；候选不计为已核验，不能据此推算真实文档准确率。

本工具复用Docling解析、OCR适配和溯源元数据。独立部分是导出关联、保守的一致性核验、页码分栏和变更报告，不把上游已有能力称为创新。一个独立的用法示例及3项测试已贡献为 [docling-core PR #917](https://github.com/docling-project/docling-core/pull/917)；本工具的运行不依赖该PR合并。

代码和测试由Mgb发起并使用OpenAI Codex辅助开发、核对。欢迎通过仓库issue提交最小自制复现，见 [贡献说明](CONTRIBUTING.md)。不要上传客户文件、案件材料、凭据或未获授权的文档。

后续维护优先核查上述扫描OCR首次运行问题，继续使用自制样本、保留首次失败及重试证据，优先检查Docling和ocrmac已有能力。修复后重新执行完整回归，不以降低阈值或跳过扫描测试代替修复。
