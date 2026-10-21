# 使用示例

在项目根目录执行，先按 [安装说明](install.md) 准备本地模型。以下只使用自制样本，不接收URL，不上传PDF。输出是文件，不需要启动服务或打开端口。

## 一份原生PDF的三类输出

```sh
.venv/bin/cntrace convert fixtures/contract.pdf --out output/contract
```

预期退出0，目录中只有document.md、provenance.json、check-report.md。Markdown供阅读；JSON保存文件完整哈希、实际页序、可识别印刷页码、原文与位置、版本和稳定编号；报告说明检查范围和失败。原PDF仍须保留。

## 查询唯一、重复和不存在的摘录

```sh
.venv/bin/cntrace verify fixtures/contract.pdf \
  --bundle output/contract --quote '保修期限'

.venv/bin/cntrace verify fixtures/contract.pdf \
  --bundle output/contract --quote '50,000.00' \
  --report output/examples/duplicate-amount.md

.venv/bin/cntrace verify fixtures/contract.pdf \
  --bundle output/contract --quote '不存在的摘录'
```

| 查询 | 退出码 | query.status | 含义 |
| --- | --- | --- | --- |
| 保修期限 | 0 | located_in_region | 位于PDF实际第3页对应文本区域；不是这几个字的单字包围框 |
| 50,000.00 | 1 | ambiguous | 实际第2、3页都有候选；没有选择第一处 |
| 不存在的摘录 | 1 | unresolved | 没有可靠候选，不填页码 |

金额50,000.00与50000.00不互换；中文数字不转成阿拉伯数字；仅忽略空白。任意AI改写、概括或意译不作语义匹配。

## 扫描与混合PDF

```sh
.venv/bin/cntrace convert fixtures/scan_contract.pdf \
  --out output/scan_contract --ocr mac

.venv/bin/cntrace verify fixtures/hybrid.pdf \
  --bundle output/hybrid --quote 'HX-02'

.venv/bin/cntrace verify fixtures/hybrid.pdf \
  --bundle output/hybrid --quote '30,000.00'
```

扫描转换保存三份输出，但因OCR待核对而退出1。HX-02在实际第2页有候选，query.status为needs_review；30,000.00跨原生页与扫描页重复，返回ambiguous。不会因原生页较可靠就自动选它。关闭OCR处理扫描页时明确报告不支持。

## 修改摘录或PDF

不要直接覆盖原件。将某份输出复制到tmp下，只在副本document.md中改金额，再用原PDF核对：应报告excerpt_changed及导出与来源不一致。删除编号标记会报告anchor_missing；新增无关联文字会报告untracked_markdown_or_broken_anchor。

修改PDF后，即使只是元数据或尾部注释，也会出现source_changed，旧位置全部暂停认定有效。它不表示程序已经确定哪段正文改变。可重复生成的副本示例在运行acceptance.py后位于output/check-examples和tmp/acceptance。

## 页码与复杂表格

page_labels样本的实际页序为1、2、3，PDF内部标签是i、A-10、A-11；印刷页码另有21，最后一页的22与99为歧义。不能把这三类数值互换。扫描页脚另列OCR候选，不作为确认印刷页码。

table_three_pages与table_no_header按页保留片段。creditors_merged的组合列名不是连续原文，因此表格摘录为unresolved，虽然原单元格坐标仍可核对。不要把这一报告抹掉，也不要在没有复核时把JSON状态手改为verified。

范围和未实现项见 [已知限制](limitations.md)，各样本文件见 [导航](samples.md)。
