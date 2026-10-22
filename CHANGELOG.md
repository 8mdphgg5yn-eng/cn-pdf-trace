# 更新说明

## v0.2.1（试用版，2026-10-22）

本版以GitHub试用版提供，不发布到PyPI。相对v0.2.0，主要调整依赖安装来源、第三方声明和安装说明，不新增平台功能。扫描OCR首次运行不稳定作为已知问题保留，后续维护优先处理。

### 依赖与许可声明

- 在保留pyproject.toml和uv.lock、按[安装说明](docs/install.md)使用uv冻结安装时，Linux的torch 2.14.1及torchvision 0.29.1来自PyTorch官方CPU索引，构建版本带`+cpu`。macOS继续使用PyPI构建。依赖锁由107个包条目减为90个，不再列出NCCL、NVSHMEM、CUDA/NVIDIA独立依赖包或triton；其他共同依赖版本保持不变。
- 补齐Docling商标归属和独立项目说明；明确本项目MIT仅覆盖自有内容，模型、字体、系统框架和其他依赖分别适用各自条款。原v0.2.0中NCCL及NVSHMEM发行包的许可声明差异作为历史核查保留，详见[第三方说明](third_party/NOTICE.md)。
- 列明torch实际构建的复合许可声明及torchvision的BSD三条款来源。排除NCCL/NVSHMEM独立依赖包不等于删除其他包中的相关许可文字，也不等于全部内嵌组件已审清。
- wheel和源码包均随附本项目MIT、Docling及docling-core的MIT全文、Noto Sans SC的OFL全文和NOTICE。源码包含自制PDF内嵌字体子集，wheel不含字体数据，因此不设置概括整个归档的统一License-Expression；项目自有内容的MIT不变。

### 安装与版本

- 完整复现使用`cn_pdf_trace-0.2.1.tar.gz`或对应完整源码，内含冻结锁、资源锁、10份自制PDF、测试、示例和说明。`cn_pdf_trace-0.2.1-py3-none-any.whl`只含应用模块及包元数据，不是独立可执行程序或离线依赖包。
- 普通pip安装wheel不会读取uv的来源配置，不能保证排除Linux CUDA依赖；仅选择CPU运行也不能改变已安装依赖。推荐本版源码加uv冻结锁的安装方式。
- 包元数据、运行时版本与溯源JSON的`tool_version`统一为0.2.1，合同示例重新生成。版本参与配置指纹及摘录编号计算，升级后重新转换同一PDF会产生新编号；旧PDF与其原有三类输出应成套保留，不应把新旧文件混用。
- 数据格式仍为schema 2，页码分栏、OCR候选待核对、重复金额歧义和跨页表格按页保留等行为保持原有边界，不宣称新增OCR或上游溯源能力。
- 干净复现脚本保留CHANGELOG及随包examples，避免新副本缺少README引用的说明；演示和回归仍重新生成输出，不使用随包示例充当测试真值。

### 验证与限制

运行验证范围仍为macOS arm64、Python 3.12；Linux x86_64和aarch64只核对CPU依赖来源与安装计划，未执行Linux PDF转换或OCR。具体测试记录见[测试说明](docs/testing.md)及随源码提供的docs/validation.json。

本轮新增空缓存复核的首次回归为56项通过、8项失败，出现扫描文字缺失及运行不一致。相同环境重新生成演示后64项通过。诊断捕获Apple Vision计算后端错误，但根因尚未闭合；首次失败与重试通过分别记录，不宣称首次从零完整复现通过。本版作为带此已知问题的试用版提供，修复情况在后续维护更新中记录。

不捆绑第三方Python环境、模型权重、独立字体或容器。不以本次核对保证所有传递依赖及内嵌组件的全部权利已经审清。哈希只用于一致性核验，不证明司法真实性。
