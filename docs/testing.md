# 回归与从零复现

完整回归目前实测于macOS arm64、Python 3.12；OCR使用Docling已有的macOS Vision接口，其他系统尚未验证完整扫描流程。安装步骤见 [安装说明](install.md)。

v0.2.1最初的待核整理曾在已有缓存环境中64项通过。本轮从修正后的源码包、新虚拟环境及空依赖和模型缓存复核：安装、下载校验、断网探针和两次生成均通过，但首次完整回归56项通过、8项失败，集中在扫描OCR覆盖和重复运行一致性。同环境重新生成演示后，原封不动的64项测试全部通过，无错误或跳过。首次失败现场单独保留，未替换为重试结果。

诊断在现有ocrmac调用中捕获Apple Vision的`e5rt_execution_stream_operation_create_precompiled_compute_operation_with_options call failed`错误；单独调用Vision又能正常返回文字。已比对的依赖文件与样本字节一致，但底层原因及其与沙箱或资源状态的关系尚未确定。没有修改第三方OCR实现、验收阈值或用旧输出充当新结果；本版作为带此已知问题的试用版提供，不能宣称首次空缓存完整复现已通过。具体范围及两次结果见[validation.json](validation.json)。

```sh
.venv/bin/python scripts/prepare_assets.py
.venv/bin/python scripts/make_fixtures.py
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

64项回归包括实际转换、区域与绘制时真值比较、重复文字与金额歧义、三类页码、文件和摘录变化、来源JSON变化、扫描候选、跨页表格，以及相同输入多次运行的确定性。先运行run_demo，测试需要它生成的基线；fixtures/gold.json来自绘制指令，不来自解析输出。

已验证基线为10份、21页、100条摘录：76条已核验、22条待人工核对、2条导出与来源不一致。原生绘制检查点230/230覆盖，扫描候选29/34匹配，5项未匹配；这些候选均不计为已核验。测试通过也包含正确报告失败、歧义和不支持，不能称为100%定位成功。

`verified`只表明Markdown文字与来源片段、来源区域与PDF原生文字层相符。隐藏文字、OCR漏段、视觉画面及真实文档准确率均不由这些机械测试证明。

从新源码副本、空依赖缓存及空模型缓存复现，不需要旧输出：

```sh
.venv/bin/python scripts/reproduce_clean.py --dest tmp/clean-check-new
```

脚本拒绝覆盖已存在的目标目录。它保留result.json、各阶段日志、新虚拟环境和处理现场；系统网络沙箱探针必须实际拒绝连接，所有64项回归必须无失败、错误或跳过。两次生成的10份PDF及gold.json须字节一致。基础Python、uv、curl及操作系统Vision仍是已有前提，不是全新操作系统测试。

源码中包含10份自制PDF；首次测试前再次生成。PDF内嵌开放字体子集，许可见 [第三方说明](../third_party/NOTICE.md)。模型权重、字体文件、依赖环境和本地输出不随源码分发，须显式下载或生成。
