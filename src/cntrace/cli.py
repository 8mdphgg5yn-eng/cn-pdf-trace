"""CLI with local conversion and verification only."""

import argparse
import json
from pathlib import Path

from .core import convert, verify, write_report


def main():
    p = argparse.ArgumentParser(description="中文 PDF 原文定位与一致性核对（本地演示）")
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("convert", help="本地 PDF 导出 Markdown、溯源 JSON、核对报告")
    c.add_argument("pdf", type=Path)
    c.add_argument("--out", type=Path, required=True)
    c.add_argument("--models", type=Path, default=Path(".cache/models"))
    c.add_argument("--ocr", choices=["off", "mac"], default="off",
                   help="显式启用Docling本地OCR；扫描候选仍需人工核对")
    v = sub.add_parser("verify", help="检查现有输出，不加载模型或重新 OCR")
    v.add_argument("pdf", type=Path)
    v.add_argument("--bundle", type=Path, required=True)
    v.add_argument("--quote", help="查询脱离来源的摘录，返回全部候选")
    v.add_argument("--report", type=Path, help="另存核对报告；默认仅打印 JSON")
    args = p.parse_args()
    try:
        if args.command == "convert":
            convert(args.pdf, args.out, args.models, ocr=args.ocr)
            report = verify(args.pdf, args.out)
            print(f"输出已生成：{args.out}；核对状态：{report['status']}")
            return 0 if report["status"] == "ok" else 1
        report = verify(args.pdf, args.bundle, quote=args.quote)
        if args.report:
            write_report(report, args.report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report.get("query") and report["query"]["status"] != "located_in_region":
            return 1
        return 0 if report["status"] == "ok" else 1
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        p.exit(2, f"无法完成：{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
