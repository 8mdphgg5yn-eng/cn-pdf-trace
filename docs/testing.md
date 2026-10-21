# 回归与从零复现

完整回归目前实测于macOS arm64、Python 3.12；OCR使用Docling已有的macOS Vision接口，其他系统尚未验证完整扫描流程。安装步骤见 [安装说明](install.md)。

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
