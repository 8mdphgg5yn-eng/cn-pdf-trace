"""Generate ten wholly synthetic PDFs and independent, drawing-time ground truth.

The gold file is created from drawing instructions, never from Docling output.
No client names, transactions, or real legal assertions are used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from fontTools.ttLib import TTFont as OpenTypeFont
from fontTools.varLib.instancer import instantiateVariableFont

W, H = 595.2756, 841.8898
FONT = "FixtureNotoSansSC"


class Fixture:
    def __init__(self, path: Path, title: str):
        self.path = path
        self.c = canvas.Canvas(str(path), pagesize=(W, H), invariant=1, pageCompression=1)
        self.c.setTitle(title)
        self.c.setAuthor("Synthetic fixture generator")
        self.page = 1
        self.checkpoints: list[dict] = []
        self.pages: list[dict] = []

    def text(self, key: str, text: str, x: float, y: float, size: float = 12):
        self.c.setFont(FONT, size)
        self.c.setFillColorRGB(0.12, 0.15, 0.19)
        self.c.drawString(x, y, text)
        width = pdfmetrics.stringWidth(text, FONT, size)
        self.checkpoints.append({
            "id": key, "text": text, "pdf_page": self.page,
            "bbox": [round(x - 2, 3), round(H-y-size-3, 3),
                     round(x+width+2, 3), round(H-y+size*0.35+3, 3)],
            "coord_origin": "TOPLEFT", "units": "pt",
        })

    def footer(self, printed: str | None):
        self.pages.append({"pdf_page": self.page, "printed_page_label": printed})
        if printed is not None:
            self.text(f"footer-{self.page}", f"第 {printed} 页", 266, 33, 10)

    def next_page(self):
        self.c.showPage()
        self.page += 1

    def save(self):
        self.c.save()
        return {
            "pdf": self.path.name,
            "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
            "pages": self.pages,
            "checkpoints": self.checkpoints,
        }


def contract(root: Path):
    f = Fixture(root / "contract.pdf", "自制合同定位样本")
    f.text("cover-title", "设备采购合同（自制测试样本）", 80, 700, 20)
    f.text("cover-note", "所有主体与交易均为虚构，仅用于程序测试。", 80, 645)
    f.text("cover-number", "测试编号：HT-001", 80, 600)
    f.footer(None)
    f.next_page()
    f.text("body-title", "设备采购合同", 70, 760, 18)
    for key, text, y in [
        ("seller", "出卖人：虚构甲方测试单位", 705),
        ("buyer", "买受人：虚构乙方测试单位", 670),
        ("price", "第一条 合同价款为人民币100,000.00元。", 610),
        ("payment", "第二条 首期支付人民币50,000.00元。", 555),
        ("repeat-1", "双方应当保存交付记录。", 500),
        ("delivery", "第三条 设备交付地点为测试仓库。", 445),
    ]:
        f.text(key, text, 70, y)
    f.footer("1")
    f.next_page()
    f.text("cont-title", "设备采购合同（续）", 70, 760, 18)
    for key, text, y in [
        ("balance", "第四条 验收后支付人民币50,000.00元。", 690),
        ("repeat-2", "双方应当保存交付记录。", 625),
        ("warranty", "第五条 保修期限为十二个月。", 560),
        ("sign", "签署栏仅为测试文字，不含真实签名或印章。", 440),
    ]:
        f.text(key, text, 70, y)
    f.footer("2")
    return f.save()


def table(root: Path):
    f = Fixture(root / "settlement.pdf", "自制工程结算表定位样本")
    xs = [45, 100, 300, 395, 550]

    def draw_table(rows, top):
        row_h = 55
        f.c.setStrokeColorRGB(.35, .4, .45)
        for x in xs:
            f.c.line(x, top, x, top-row_h*len(rows))
        for i in range(len(rows)+1):
            f.c.line(xs[0], top-i*row_h, xs[-1], top-i*row_h)
        for i, row in enumerate(rows):
            for j, (key, text) in enumerate(row):
                f.text(key, text, xs[j]+7, top-i*row_h-31, 10)

    f.text("table-title", "工程结算表（自制测试样本）", 65, 760, 18)
    f.text("table-note", "单位：元。所有项目与金额均为测试数据。", 65, 715)
    draw_table([
        [("h1", "序号"), ("h2", "项目名称"), ("h3", "数量"), ("h4", "金额")],
        [("r1n", "01"), ("r1p", "基础施工"), ("r1q", "10"), ("r1a", "50,000.00")],
        [("r2n", "02"), ("r2p", "设备安装"), ("r2q", "20"), ("r2a", "50,000.00")],
        [("r3n", "03"), ("r3p", "跨页项目：钢构件制作"), ("r3q", "30"), ("r3a", "80,000.00")],
    ], 660)
    f.text("split-note", "记录03的说明在下一页继续，尚未形成独立新项目。", 65, 380, 11)
    f.footer("7")
    f.next_page()
    f.text("table-cont", "工程结算表（续页）", 65, 760, 18)
    draw_table([
        [("h1b", "序号"), ("h2b", "项目名称"), ("h3b", "数量"), ("h4b", "金额")],
        [("r3cn", ""), ("r3cp", "续：含运输及现场拼装"), ("r3cq", ""), ("r3ca", "")],
        [("r4n", "04"), ("r4p", "现场调试"), ("r4q", "5"), ("r4a", "20,000.00")],
        [("sum-n", "合计"), ("sum-p", "测试合计金额"), ("sum-q", ""), ("sum-a", "200,000.00")],
    ], 680)
    f.text("table-end", "本表不对应真实工程，不作为结算或付款凭证。", 65, 380, 11)
    f.footer("8")
    data = f.save()
    data["checkpoints"] = [p for p in data["checkpoints"] if p["text"]]
    data["logical_continuations"] = [{"from": "r3p", "to": "r3cp", "auto_merge": False}]
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=Path("fixtures"))
    p.add_argument("--font", type=Path, default=Path(".cache/fonts/NotoSansSC.ttf"))
    args = p.parse_args()
    if not args.font.is_file():
        p.error("缺少开放字体；先执行 scripts/prepare_assets.py，或用 --font 指定中文 TTF")
    font_lock = Path(__file__).resolve().parents[1]/"font.lock.json"
    if font_lock.is_file() and args.font.name == "NotoSansSC.ttf":
        if hashlib.sha256(args.font.read_bytes()).hexdigest() != json.loads(
            font_lock.read_text())["sha256"]:
            p.error("字体哈希与锁文件不同；拒绝覆盖已有样本")
    regular = args.font.with_name("NotoSansSC-Regular.ttf")
    # ReportLab otherwise uses the variable font's default, very thin weight.
    # Always derive from the locked source, never trust an old derived cache.
    # FontTools otherwise writes wall-clock time into head.modified, changing
    # embedded PDF bytes despite identical drawing instructions.
    variable = OpenTypeFont(str(args.font), recalcTimestamp=False)
    instantiateVariableFont(variable, {"wght": 400}, inplace=True)
    variable["head"].modified = variable["head"].created
    variable.save(regular)
    pdfmetrics.registerFont(TTFont(FONT, str(regular)))
    args.out.mkdir(parents=True, exist_ok=True)
    from phase2_fixtures import additional, policy
    data = {"schema_version": 2, "origin": "wholly synthetic; drawing-time truth",
            "font_sha256": hashlib.sha256(args.font.read_bytes()).hexdigest(),
            "documents": [policy(contract(args.out), "合同：页码偏移和重复内容", min_native=1),
                          policy(table(args.out), "两页工程结算表", min_native=1),
                          *additional(args.out)]}
    (args.out / "gold.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")
    print(f"生成10份自制PDF与独立答案：{args.out}")


if __name__ == "__main__":
    main()
