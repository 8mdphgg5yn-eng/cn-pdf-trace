"""Generate the three deliverables for all ten synthetic PDFs, offline."""

import json
import os
from pathlib import Path

from cntrace.core import MAC_OCR_AVAILABLE, build_converter, convert, offline_guard

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    model_dir = ROOT / ".cache/models"
    with offline_guard():
        converters = {}
        skipped = []
        documents = json.loads((ROOT/"fixtures/gold.json").read_text())["documents"]
        for document in documents:
            stem = Path(document["pdf"]).stem
            mode = document["ocr"]
            if mode == "mac" and not MAC_OCR_AVAILABLE:
                skipped.append(stem)
                print(f"跳过扫描样本：{stem}（需要macOS Vision OCR，当前系统不支持）", flush=True)
                continue
            if mode not in converters:
                converters[mode] = build_converter(model_dir, ocr=mode)
            print(f"转换自制样本：{stem}", flush=True)
            ledger = convert(ROOT/f"fixtures/{stem}.pdf", ROOT/f"output/{stem}",
                             model_dir, converter=converters[mode], ocr=mode)
            from collections import Counter
            print(json.dumps({"sample": stem, "records": len(ledger["records"]),
                              "status": dict(Counter(r["status"] for r in ledger["records"])),
                              "conversion": ledger["conversion"]}, ensure_ascii=False), flush=True)

    if skipped:
        print(f"已跳过{len(skipped)}份需macOS OCR的样本：{'、'.join(skipped)}。"
              "依赖这些样本的回归项会标为skip，完整回归与验收不算通过。", flush=True)


if __name__ == "__main__":
    main()
