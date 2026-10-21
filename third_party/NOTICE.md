# 第三方组件说明

本文件记录本版源码使用的第三方组件。项目自己的许可证不覆盖这些组件；代码、模型权重和字体分别适用各自条款。完整源码不打包第三方Python环境、模型权重或独立字体文件，也不声称仅凭依赖元数据已审查全部传递依赖。

| 组件 | 本次版本或固定来源 | 许可证信息来源 |
| --- | --- | --- |
| Docling-slim | 2.141.0 | MIT；本目录 `Docling-MIT.txt`，对应上游标签 LICENSE |
| docling-core | 2.103.1 | MIT；本目录 `DoclingCore-MIT.txt`，对应上游标签 LICENSE |
| docling-parse | 7.22.3 | 安装包元数据标记 MIT |
| docling-ibm-models | 4.0.3 | 安装包元数据标记 MIT；不等同于模型权重许可证 |
| Heron 布局模型 | `models.lock.json` 中固定提交 | 固定版本模型卡标记 Apache-2.0 |
| TableFormer accurate | `models.lock.json` 中固定提交 | 固定版本 docling-models 模型卡标记 CDLA-Permissive-2.0 |
| Noto Sans SC | `font.lock.json` 的文件哈希 | SIL OFL 1.1，全文见本目录 `NotoSansSC-OFL.txt` |
| pypdfium2 | 5.14.0 | 包元数据标记 BSD-3-Clause、Apache-2.0 及依赖许可证；PDFium 等依赖须另核 |
| pypdf | 6.21.1 | 包元数据标记 BSD-3-Clause |
| OpenCV headless | 4.14.0.94 | 包元数据标记 Apache 2.0 |
| ReportLab | 4.5.1 | 包元数据标记 BSD license，具体见原包 license.txt |
| markdown-it-py | 4.2.0 | 安装包元数据标记 MIT |
| fonttools | 4.67.0 | 包元数据标记 MIT；仅制作样本使用 |
| ocrmac | 1.0.1 | 包元数据标记 MIT license；由Docling已有OCR适配调用 |
| PyObjC core / Vision | 12.2.2 | 包元数据标记 MIT；调用本机macOS Vision |

运行资源准备脚本后，模型卡快照位于 `.cache/models/` 的对应模型目录；模型权重不纳入项目源文件。字体不作为项目字体包发布，自制 PDF 内嵌其子集，保留 OFL 声明。Python 全部解析后的依赖由 `uv.lock` 固定，其他依赖仍适用各自条款。

本项目不独立再发布或下载Apple的OCR模型。Apple系统框架不适用上述Python封装包的MIT声明，本文件不作其再分发授权判断。

上游原文：

- https://github.com/docling-project/docling/blob/v2.141.0/LICENSE
- https://github.com/docling-project/docling-core/blob/v2.103.1/LICENSE
- https://huggingface.co/docling-project/docling-layout-heron/blob/8f39ad3c0b4c58e9c2d2c84a38465abf757272d8/README.md
- https://huggingface.co/docling-project/docling-models/blob/fc0f2d45e2218ea24bce5045f58a389aed16dc23/README.md
- https://github.com/google/fonts/tree/main/ofl/notosanssc

## 源码分发范围

源码中的fixtures为程序绘制的自制PDF，不包含客户材料。内嵌的Noto Sans SC字体子集仍适用SIL OFL 1.1，保留原始版权及完整许可文本，不改用项目自己的许可证。OFL对生成文档的说明见 [官方FAQ](https://openfontlicense.org/ofl-faq/)；原始字体固定来源见font.lock.json。

安装时由uv/PyPI取得的依赖保留其原包许可与通知；模型和字体通过显式下载脚本从锁定公开版本取得，不由本仓库重新打包。若今后分发依赖wheel、模型、字体、容器或独立可执行程序，应重新核对其再分发义务，不能沿用本次“仅源码”的检查结论。

macOS Vision是可选OCR使用的Apple系统框架，不是本项目开源代码的一部分，也不随源码分发。原生文字PDF转换默认关闭OCR。
