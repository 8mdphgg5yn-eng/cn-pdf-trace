# 十份自制样本与输出导航

全部由程序绘制，不含客户材料。每份输出目录只有约定的三个文件。

| 场景 | PDF | Markdown | 溯源JSON | 核对报告 |
| --- | --- | --- | --- | --- |
| 合同：页码偏移和重复内容 | [PDF](../fixtures/contract.pdf) | [正文](../output/contract/document.md) | [来源](../output/contract/provenance.json) | [报告](../output/contract/check-report.md) |
| 两页工程结算表 | [PDF](../fixtures/settlement.pdf) | [正文](../output/settlement/document.md) | [来源](../output/settlement/provenance.json) | [报告](../output/settlement/check-report.md) |
| 债权表：同名主体、重复本金、两页重复表头 | [PDF](../fixtures/creditors.pdf) | [正文](../output/creditors/document.md) | [来源](../output/creditors/provenance.json) | [报告](../output/creditors/check-report.md) |
| 债权表：两层表头、跨列合并、重复金额 | [PDF](../fixtures/creditors_merged.pdf) | [正文](../output/creditors_merged/document.md) | [来源](../output/creditors_merged/provenance.json) | [报告](../output/creditors_merged/check-report.md) |
| 三页表格：多行单元格、续行、重复金额、表头变化 | [PDF](../fixtures/table_three_pages.pdf) | [正文](../output/table_three_pages/document.md) | [来源](../output/table_three_pages/provenance.json) | [报告](../output/table_three_pages/check-report.md) |
| 两页表格：次页无表头、空白键续行 | [PDF](../fixtures/table_no_header.pdf) | [正文](../output/table_no_header/document.md) | [来源](../output/table_no_header/provenance.json) | [报告](../output/table_no_header/check-report.md) |
| 封面、PDF页标签、印刷页码、双页脚歧义 | [PDF](../fixtures/page_labels.pdf) | [正文](../output/page_labels/document.md) | [来源](../output/page_labels/provenance.json) | [报告](../output/page_labels/check-report.md) |
| 清晰中文扫描：重复条款和金额 | [PDF](../fixtures/scan_contract.pdf) | [正文](../output/scan_contract/document.md) | [来源](../output/scan_contract/provenance.json) | [报告](../output/scan_contract/check-report.md) |
| 低清灰度扫描：小字、相似数字和重复金额 | [PDF](../fixtures/scan_degraded.pdf) | [正文](../output/scan_degraded/document.md) | [来源](../output/scan_degraded/provenance.json) | [报告](../output/scan_degraded/check-report.md) |
| 混合PDF：原生文字页与扫描页、跨来源重复金额 | [PDF](../fixtures/hybrid.pdf) | [正文](../output/hybrid/document.md) | [来源](../output/hybrid/provenance.json) | [报告](../output/hybrid/check-report.md) |

[回归与验收说明](testing.md)列明覆盖分母、实际失败、OCR差异和成本。测试通过不表示每条摘录都已核验。
