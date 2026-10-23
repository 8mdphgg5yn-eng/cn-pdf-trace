"""Check delivered bundles against drawing-time truth; save reviewable examples."""

from __future__ import annotations

import json
import argparse
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from cntrace.core import verify, write_report
from fixture_metrics import evaluate

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="用绘制答案核对演示及pytest回执")
    parser.add_argument("--junit", type=Path, default=Path("output/phase2-regression.xml"))
    parser.add_argument("--out", type=Path, default=Path("output/phase2-acceptance.json"))
    args = parser.parse_args()
    gold = json.loads((ROOT/"fixtures/gold.json").read_text())
    summary = {"scope": "ten wholly synthetic PDFs; OCR candidates are not verified",
               "documents": []}
    for document in gold["documents"]:
        stem = Path(document["pdf"]).stem
        bundle = ROOT/"output"/stem
        if not (bundle/"provenance.json").is_file():
            raise SystemExit(f"缺少样本输出 {bundle}（非macOS会跳过扫描样本）；验收不通过")
        ledger = json.loads((bundle/"provenance.json").read_text())
        report = verify(ROOT/"fixtures"/document["pdf"], bundle)
        metrics = evaluate(document, ledger)
        assert not metrics["false_successes"], metrics
        for name, policy in (("native_region_points", "min_native_verified_coverage"),
                             ("ocr_candidate_points", "min_ocr_candidate_coverage")):
            if metrics[name]["total"]:
                assert metrics[name]["rate"] >= document["acceptance"][policy], metrics
        metrics.update({"conversion": ledger["conversion"], "report_status": report["status"],
                        "finding_counts": dict(Counter(
                            f["kind"] for f in report["findings"]))})
        summary["documents"].append(metrics)
    xml = ROOT/args.junit
    if xml.is_file():
        suites = ET.parse(xml).getroot().findall("testsuite")
        summary["regression"] = {
            key: sum(int(s.get(key, "0")) for s in suites)
            for key in ("tests", "failures", "errors", "skipped")}
        assert summary["regression"]["tests"] > 0
        assert not any(summary["regression"][x] for x in ("failures", "errors", "skipped"))
    else:
        raise SystemExit(f"先运行 pytest 并生成 {args.junit}")
    target = ROOT/args.out
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")

    samples = ROOT/"output/check-examples"
    samples.mkdir(parents=True, exist_ok=True)
    original = ROOT/"output/contract"
    pdf = ROOT/"fixtures/contract.pdf"
    for name, quote in (("ambiguous", "50,000.00"), ("unresolved", "不存在的原文片段")):
        write_report(verify(pdf, original, quote=quote), samples/f"{name}.md")
    work = ROOT/"tmp/acceptance"
    work.mkdir(parents=True, exist_ok=True)
    edited = work/"edited"
    shutil.copytree(original, edited, dirs_exist_ok=True)
    md = edited/"document.md"
    md.write_text(md.read_text().replace("100,000.00", "900,000.00", 1))
    write_report(verify(pdf, edited), samples/"excerpt-changed.md")
    changed = work/"source-changed.pdf"
    changed.write_bytes(pdf.read_bytes()+b"\n% synthetic byte-only change\n")
    write_report(verify(changed, original), samples/"source-changed.md")
    for stem in ("creditors_merged", "page_labels", "scan_degraded"):
        write_report(verify(ROOT/f"fixtures/{stem}.pdf", ROOT/f"output/{stem}"),
                     samples/f"{stem}.md")
    write_report(verify(ROOT/"fixtures/hybrid.pdf", ROOT/"output/hybrid", quote="HX-02"),
                 samples/"ocr-candidate.md")
    print(json.dumps({"regression": summary["regression"],
                      "documents": [{k: v for k, v in d.items() if k != "coverage"}
                                    for d in summary["documents"]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
