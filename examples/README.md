# 三类输出示例

contract-output由v0.2.1对本仓库fixtures/contract.pdf实际转换生成，与该PDF的SHA-256关联，仅含自制文字。可以直接查看Markdown、来源JSON及核对报告，无需先下载模型。

这些是本机已验证环境的一次输出，含解析器版本和本次耗时，不是跨系统精度或性能承诺。完整回归会在output下重新生成10份结果，不把本示例当作解析器的绘制真值。

```sh
.venv/bin/cntrace verify fixtures/contract.pdf --bundle examples/contract-output
```
