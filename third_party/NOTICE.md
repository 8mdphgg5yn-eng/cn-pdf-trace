# 第三方组件说明

本文件列出本版主要第三方组件及需要说明的许可边界，不是全部传递依赖的逐文件许可清单。项目自己的许可证不覆盖这些组件；代码、模型权重和字体分别适用各自条款。完整源码不打包第三方Python环境、模型权重或独立字体文件，也不声称仅凭依赖元数据已审查全部传递依赖。

v0.2.1试用版的uv锁有90个包条目，包含torch和torchvision的平台构建变体；它不列出NCCL、NVSHMEM、CUDA/NVIDIA独立依赖包或triton。Linux在保留uv源配置并使用冻结锁时取得官方CPU构建。该保证不覆盖普通pip独立解析或用户自行改锁的环境，也不证明未核对的Windows等构建没有内嵌GPU组件。下文五个NVIDIA相关包的核查针对原公开v0.2.0的107条目锁，作为历史许可依据保留，不能理解为当前v0.2.1仍包含这些独立依赖包。切换CPU构建不等于已经完成所有新构建内嵌组件的许可审计。

| 组件 | 本次版本或固定来源 | 许可证信息来源 |
| --- | --- | --- |
| Docling-slim | 2.141.0 | MIT；本目录 `Docling-MIT.txt`，对应上游标签 LICENSE |
| docling-core | 2.103.1 | MIT；本目录 `DoclingCore-MIT.txt`，对应上游标签 LICENSE |
| docling-parse | 7.22.3 | 安装包元数据标记 MIT |
| docling-ibm-models | 4.0.3 | 安装包元数据标记 MIT；不等同于模型权重许可证 |
| torch / PyTorch | macOS 2.14.1；Linux锁定2.14.1+cpu | 实际构建元数据使用复合License-Expression，涉及Apache-2.0、LLVM例外、BSD-2-Clause、BSD-3-Clause、BSL-1.0和MIT；包内主LICENSE及third_party许可须一并保留，不能仅概括为项目MIT或单一BSD |
| torchvision | macOS 0.29.1；Linux锁定0.29.1+cpu | 元数据标记BSD；已核对的包内主LICENSE为BSD三条款，其他随包许可仍须保留 |
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
- https://github.com/google/fonts/blob/47d54ca1ebb14fd864695f1d39dc734f39017c33/ofl/notosanssc/OFL.txt

## 源码分发范围

源码中的fixtures为程序绘制的自制PDF，不包含客户材料。内嵌的Noto Sans SC字体子集仍适用SIL OFL 1.1，保留原始版权及完整许可文本，不改用项目自己的许可证。OFL对生成文档的说明见 [官方FAQ](https://openfontlicense.org/ofl-faq/)；原始字体固定来源见font.lock.json。

安装时由uv从配置索引取得的依赖保留其原包许可与通知；模型和字体通过显式下载脚本从锁定公开版本取得，不由本仓库重新打包。若今后分发依赖wheel、模型、独立字体文件、容器或独立可执行程序，应重新核对其再分发义务，不能沿用本次仅分发本项目代码、文档、自制PDF及许可声明的检查结论。

torch的完整元数据表达式为`Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT`。上述torch及torchvision声明核对了本机macOS包，以及锁定Linux x86_64、aarch64的Python 3.12 CPU wheel元数据和主许可文件，不代表已经逐项核对全部内嵌组件或其他平台构建。包内可能保留GPU相关第三方许可文字，不能仅凭许可文件名推断存在可用的CUDA/NCCL运行库；本版排除的是独立依赖包链。CPU索引和冻结锁的用法见[uv官方说明](https://docs.astral.sh/uv/concepts/indexes/)。

本项目自有内容继续采用MIT，PDF内嵌字体仍适用OFL；OFL不因此改变文档本身的许可。源码包含这些PDF，wheel不含字体数据，两者携带内容不同。为避免将整个归档的全部内容概括为MIT，当前pyproject.toml不设置统一的License-Expression，仅通过license-files随附本项目MIT、相关第三方许可全文及本说明。它不表示项目缺少许可证，也不把外部安装的依赖许可证并入项目许可。元数据字段的范围见 [PyPA规范](https://packaging.python.org/en/latest/specifications/core-metadata/#license-expression)。

macOS Vision是可选OCR使用的Apple系统框架，不是本项目开源代码的一部分，也不随源码分发。原生文字PDF转换默认关闭OCR。

## 商标与其他许可边界

Docling™ 是 LF Projects, LLC 的商标。本项目独立维护；引用 Docling 名称仅说明技术依赖，不表示官方维护、认可或认证。开源代码许可不等同于商标授权，参见 [LF Projects 商标政策](https://lfprojects.org/policies/trademark-policy/)。

`uv.lock` 中的全部依赖并非都采用MIT。本次锁定版本中，certifi 2026.10.19的安装包元数据标记MPL-2.0，tqdm 4.70.1标记MPL-2.0 AND MIT；这些依赖由安装工具单独取得，保留各自许可。

原公开v0.2.0锁在适用的Linux平台可经torch引入CUDA/NVIDIA依赖，例如nvidia-cublas和nvidia-cusolver的发布元数据标注NVIDIA专有许可证。仅选择CPU运行不能改变旧锁的依赖；v0.2.1通过指定CPU安装来源避开这条依赖链。此类组件不由本项目重新许可为MIT，原版或自选CUDA环境的使用及再分发仍应另核实际包内条款及 [NVIDIA许可协议](https://docs.nvidia.com/cuda/eula/index.html)。本项目不打包这些二进制，也未完成Linux实际运行及所有平台二进制许可的逐项审查。

原版许可元数据清点覆盖107个包条目（含本项目）：85个本机已安装包及22个其他平台条目。PyPI JSON中五个条目的许可字段为空，但进一步读取原锁定发行包发现，四个组件的wheel内METADATA实际标记LicenseRef-NVIDIA-Proprietary；不能将JSON空字段理解为无许可。对这五个包的核对如下，仍不等于对107个包全部内嵌二进制许可作了审查。

## 原v0.2.0五个Linux条件依赖的发行包核对

本节核对对象为原公开v0.2.0的uv.lock中的一个通用wheel，以及四个组件各自的Linux aarch64、x86_64 wheel，共九个发行文件，均不在当前CPU锁中。四组不同架构wheel的对应许可全文分别相同。这里只说明实际读取到的文件与适用边界，不为第三方重新许可，也不把源码许可直接套用为预编译包的无条件授权。

| 锁定包 | 包内实际许可及核对结果 | 使用与再分发边界 |
| --- | --- | --- |
| [cuda-toolkit 13.0.3.0](https://pypi.org/project/cuda-toolkit/13.0.3.0/) | 只有METADATA、WHEEL、RECORD三个元数据文件，无程序实现、无独立许可全文；通过extras选择实际组件 | 不能替它补写MIT或推定全部组件采用同一许可。组件按各自条款使用；若另行再分发该元数据包，应先确认其元数据内容的授权 |
| [nvidia-cuda-runtime 13.0.96](https://pypi.org/project/nvidia-cuda-runtime/13.0.96/) | 附2018年NVIDIA SDK协议、CUDA补充条款及第三方许可附件；属于专有SDK条款，不是MIT | CUDA补充条款限定开发应用用于含NVIDIA GPU的系统，附件列出可分发的libcudart等文件；再分发须满足通用条件，不能据此宣称整包任意再分发。SDK附件提及的其他组件不等于本wheel实际包含它们 |
| [nvidia-cudnn-cu13 9.24.0.43](https://pypi.org/project/nvidia-cudnn-cu13/9.24.0.43/) | 附2020年NVIDIA SDK协议及cuDNN补充条款；属于专有SDK条款 | 补充条款限定开发应用用于含NVIDIA GPU的系统，列明.so、.h等可分发部分；仍受附加功能、应用访问、保留权利声明等条件约束，不改用项目MIT |
| [nvidia-nccl-cu13 2.30.7](https://pypi.org/project/nvidia-nccl-cu13/2.30.7/) | wheel许可正文为BSD三条款并指向NVTX许可，但METADATA标记专有；[同版本源码标签的许可](https://github.com/NVIDIA/nccl/blob/73cf112295c33aee2b895f329f592f2a9b4b0f97/LICENSE.txt)另列Apache-2.0及保留BSD部分 | 发行文件存在许可声明不一致，不应只凭一个标签认定整个预编译包全部专有或全部BSD。未来捆绑分发前，应澄清适用范围，并核对[NVTX第三方声明](https://github.com/NVIDIA/nccl/blob/73cf112295c33aee2b895f329f592f2a9b4b0f97/ThirdPartyNotices.txt)；已识别的BSD部分须保留版权、条件和免责文本，不得暗示权利人背书 |
| [nvidia-nvshmem-cu13 3.4.5](https://pypi.org/project/nvidia-nvshmem-cu13/3.4.5/) | wheel的License.txt与上述CUDA runtime文件完全相同，未载NVSHMEM专用补充条款；[同版本源码的许可](https://github.com/NVIDIA/nvshmem/blob/131da55f643ac87c810ba0bc51d359258bf433a1/License.txt)则明确为NVIDIA SDK协议、NVSHMEM补充条款及额外第三方许可 | 专有SDK许可性质已确认。源码补充条款允许按协议条件分发SDK部分，并非可改为MIT；它及额外第三方声明在wheel随附文件中的缺口仍需澄清，不能声称这个预编译包的再分发已审清 |

上述许可文件包含使用范围、第三方权利、免责、出口及其他合同条件，表格只是概括，实际使用须阅读具体版本全文。当前项目不随源码包或wheel分发这些组件，不提供捆绑它们的离线包或容器；NCCL、NVSHMEM的发行声明差异已明确列出，不以本项目NOTICE代替发布者澄清，也不修改第三方包内的许可文件。

本说明不替代具体版本的原始许可。模型卡标记Apache-2.0或CDLA-Permissive-2.0，不等于独立核实了所有训练数据的权利链；本仓库不提供模型权重再分发包。若后续分发权重，应另行核对并随附适用许可文本。
