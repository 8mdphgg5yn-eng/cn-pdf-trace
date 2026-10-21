"""Eight additional synthetic fixtures. Gold comes only from drawing instructions."""

from __future__ import annotations

import copy
import hashlib
from io import BytesIO

import pypdfium2 as pdfium
from PIL import ImageEnhance, ImageFilter
from pypdf import PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from make_fixtures import Fixture, W, H


def grid(f, rows, *, top=665, xs=(42, 95, 300, 405, 553), height=55, key="t"):
    f.c.setStrokeColorRGB(.3, .35, .4)
    for x in xs:
        f.c.line(x, top, x, top-height*len(rows))
    for i in range(len(rows)+1):
        f.c.line(xs[0], top-i*height, xs[-1], top-i*height)
    for i, row in enumerate(rows):
        for j, text in enumerate(row):
            for line, value in enumerate(text.split("\n")):
                if value:
                    f.text(f"{key}-{i}-{j}-{line}", value, xs[j]+6,
                           top-i*height-25-line*16, 10)


def policy(data, scenario, *, ocr="off", min_native=.75, min_ocr=0):
    data["scenario"] = scenario
    data["ocr"] = ocr
    # Declared before extraction; rejection alone cannot satisfy coverage.
    data["acceptance"] = {"min_native_verified_coverage": min_native,
                          "min_ocr_candidate_coverage": min_ocr}
    for cp in data["checkpoints"]:
        cp.setdefault("text_origin", "native")
    for page in data["pages"]:
        page.setdefault("text_origin", "native")
    return data


def creditors(root):
    f = Fixture(root/"creditors.pdf", "自制债权表")
    for p in range(2):
        f.text(f"title-{p}", "债权申报核对表（虚构测试）", 55, 758, 18)
        f.text(f"note-{p}", "仅为软件样本，申报金额不代表确认债权。", 55, 710, 11)
        rows = [["编号", "债权人", "申报本金", "申报利息", "测试合计"]]
        rows += [[f"{p*3+i:02}", f"虚构{['甲','乙','丙'][i-1]}企业", "80,000.00",
                  f"{i},000.00", f"8{i},000.00"] for i in range(1, 4)]
        grid(f, rows, xs=(40, 85, 225, 335, 445, 555), key=f"p{p}")
        f.text(f"status-{p}", "状态：待核对；主体、金额均为自制测试数据。", 55, 365, 11)
        f.footer(str(11+p))
        if p == 0:
            f.next_page()
    return policy(f.save(), "债权表：同名主体、重复本金、两页重复表头", min_native=.95)


def creditors_merged(root):
    f = Fixture(root/"creditors_merged.pdf", "合并单元格债权表")
    f.text("title", "债权分类表（自制合并单元格样本）", 50, 760, 17)
    f.text("note", "表中分类为虚构字段，不表达法律认定。", 50, 715, 11)
    xs = [40, 95, 235, 340, 445, 555]
    top, h = 655, 45
    for x in xs:
        f.c.line(x, top if x in xs[:2]+xs[-1:] else top-h, x, top-6*h)
    # Group heading spans the three amount columns, left headings span two rows.
    f.c.line(xs[2], top, xs[2], top-6*h)
    for i in (0, 2, 3, 4, 5, 6):
        f.c.line(xs[0], top-i*h, xs[-1], top-i*h)
    f.c.line(xs[2], top-h, xs[-1], top-h)
    for key, text, x, y in [("n", "编号", 48, 603), ("who", "债权人", 105, 603),
                             ("group", "申报金额", 355, 627), ("principal", "本金", 258, 582),
                             ("interest", "利息", 365, 582), ("total", "合计", 472, 582)]:
        f.text(key, text, x, y, 11)
    for i, row in enumerate([
        ["M01", "虚构丁企业", "60,000.00", "6,000.00", "66,000.00"],
        ["M02", "虚构戊企业", "60,000.00", "0.00", "60,000.00"],
        ["M03", "虚构己企业", "90,000.00", "9,000.00", "99,000.00"],
        ["合计", "测试汇总", "210,000.00", "15,000.00", "225,000.00"],
    ]):
        for j, text in enumerate(row):
            f.text(f"r{i}c{j}", text, xs[j]+6, top-(i+2)*h-27, 10)
    f.text("tail", "保留原单元格跨度；不以空白单元格推断零金额。", 50, 330, 11)
    f.footer("23")
    return policy(f.save(), "债权表：两层表头、跨列合并、重复金额", min_native=.75)


def table_three_pages(root):
    f = Fixture(root/"table_three_pages.pdf", "三页工程明细")
    pages = [
        [["序号", "施工内容", "数量", "金额"],
         ["C01", "围护施工", "10", "30,000.00"],
         ["C02", "管道施工", "20", "30,000.00"],
         ["C03", "钢结构制作\n含构件预处理", "30", "90,000.00"]],
        [["序号", "施工内容", "数量", "金额"],
         ["", "续C03：运输及吊装\n接上一页记录", "", ""],
         ["C04", "设备就位\n含基础找平", "5", "20,000.00"],
         ["C05", "消防系统布线\n说明在下一页继续", "15", "40,000.00"]],
        [["序号", "施工内容（续）", "数量", "金额"],
         ["", "续C05：联动测试\n接上一页记录", "", ""],
         ["C06", "现场清理", "1", "5,000.00"],
         ["合计", "自制测试汇总", "", "215,000.00"]],
    ]
    for i, rows in enumerate(pages):
        f.text(f"title-{i}", "工程分项明细（三页自制样本）", 50, 760, 18)
        f.text(f"note-{i}", "多行说明跨页；页内表头不必完全相同。", 50, 715, 11)
        grid(f, rows, height=75, key=f"p{i}")
        f.text(f"tail-{i}", "不得仅凭空序号合并记录；原始页内片段应保留。", 50, 300, 11)
        f.footer(str(31+i))
        if i < 2:
            f.next_page()
    data = f.save()
    data["logical_continuations"] = [{"from_page": 1, "to_page": 2, "record": "C03"},
                                     {"from_page": 2, "to_page": 3, "record": "C05"}]
    return policy(data, "三页表格：多行单元格、续行、重复金额、表头变化", min_native=.75)


def table_no_header(root):
    f = Fixture(root/"table_no_header.pdf", "无重复表头续表")
    rows = [
        [["序号", "项目说明", "数量", "金额"], ["D01", "路面施工", "12", "70,000.00"],
         ["D02", "排水施工\n后续说明见次页", "8", "40,000.00"]],
        [["", "续D02：井室及收口\n本页未重复表头", "", ""],
         ["D03", "铺装施工", "12", "70,000.00"],
         ["合计", "自制合计", "", "180,000.00"]],
    ]
    for i in range(2):
        f.text(f"title-{i}", "工程续表（无重复表头测试）", 50, 760, 18)
        grid(f, rows[i], top=670, height=80, key=f"p{i}")
        f.text(f"tail-{i}", "正文片段继续不等于已经识别为同一逻辑表。", 50, 355, 11)
        f.footer(str(41+i))
        if i == 0:
            f.next_page()
    return policy(f.save(), "两页表格：次页无表头、空白键续行", min_native=.75)


def page_labels(root):
    f = Fixture(root/"page_labels.pdf", "页标签与印刷页码")
    for i in range(3):
        f.text(f"title-{i}", "页码与文件内部标签测试", 55, 755, 18)
        f.text(f"body-{i}", f"自制页面P{i+1}，实际页序与印刷页码分别记录。", 55, 650)
        if i == 0:
            f.footer(None)
        elif i == 1:
            f.footer("21")
        else:
            f.pages.append({"pdf_page": 3, "printed_page_label": None,
                            "printed_label_status": "ambiguous",
                            "printed_label_candidates": ["22", "99"]})
            f.text("footer-left", "第 22 页", 100, 33, 10)
            f.text("footer-right", "第 99 页", 400, 33, 10)
        if i < 2:
            f.next_page()
    data = f.save()
    writer = PdfWriter(clone_from=f.path)
    writer.set_page_label(0, 0, style="/r")
    writer.set_page_label(1, 2, style="/D", prefix="A-", start=10)
    with f.path.open("wb") as stream:
        writer.write(stream)
    data["sha256"] = hashlib.sha256(f.path.read_bytes()).hexdigest()
    for p, label in zip(data["pages"], ["i", "A-10", "A-11"], strict=True):
        p["pdf_page_label"] = label
    return policy(data, "封面、PDF页标签、印刷页码、双页脚歧义", min_native=1)


def rasterize(f, data, *, pages, degraded=False):
    """Render our own drawings and rebuild an image-only page at the same size."""
    original = f.path.read_bytes()
    source = pdfium.PdfDocument(original)
    buf = BytesIO()
    out = canvas.Canvas(buf, pagesize=(W, H), invariant=1, pageCompression=1)
    out.setTitle("自制扫描或混合文字层样本")
    out.setAuthor("Synthetic fixture generator")
    for i in range(len(source)):
        if i+1 not in pages:
            # Native pages are inserted below with pypdf; only image pages here.
            out.showPage()
            continue
        page = source[i]
        bitmap = page.render(scale=1 if degraded else 2)
        image = bitmap.to_pil().copy()
        if degraded:
            image = ImageEnhance.Contrast(image.convert("L")).enhance(.6)
            image = image.filter(ImageFilter.GaussianBlur(.65))
        out.drawImage(ImageReader(image), 0, 0, width=W, height=H)
        out.showPage()
        bitmap.close()
        page.close()
    out.save()
    source.close()
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(original))
    scan = PdfReader(BytesIO(buf.getvalue()))
    writer = PdfWriter()
    for i in range(len(reader.pages)):
        writer.add_page(scan.pages[i] if i+1 in pages else reader.pages[i])
    writer.add_metadata({"/Title": "自制扫描或混合文字层样本", "/Producer": "synthetic-rasterizer-v1"})
    with f.path.open("wb") as stream:
        writer.write(stream)
    data = copy.deepcopy(data)
    data["sha256"] = hashlib.sha256(f.path.read_bytes()).hexdigest()
    for entry in data["pages"]+data["checkpoints"]:
        entry["text_origin"] = "ocr" if entry["pdf_page"] in pages else "native"
    return data


def scan_contract(root):
    f = Fixture(root/"scan_contract.pdf", "清晰扫描测试")
    for i in range(2):
        f.text(f"title-{i}", "扫描合同（完全自制测试）", 55, 760, 18)
        for j, text in enumerate(["甲方：虚构扫描甲单位", "乙方：虚构扫描乙单位",
                                  "测试金额为人民币30,000.00元。", "同一款项应当保留核对记录。",
                                  "本文件为图像测试，不含真实签章。"]):
            f.text(f"p{i}-line{j}", text, 55, 680-j*65, 13)
        f.footer(str(51+i))
        if i == 0:
            f.next_page()
    data = rasterize(f, f.save(), pages={1, 2})
    return policy(data, "清晰中文扫描：重复条款和金额", ocr="mac", min_native=0, min_ocr=.7)


def scan_degraded(root):
    f = Fixture(root/"scan_degraded.pdf", "低清扫描测试")
    f.text("title", "低清债权表扫描样本", 55, 760, 16)
    grid(f, [["编号", "虚构债权人", "申报金额", "备注"],
             ["S01", "虚构扫描丙", "8,888.88", "待核对"],
             ["S02", "虚构扫描丁", "8,888.88", "待核对"]],
         xs=(45, 105, 285, 420, 555), height=70, key="scan")
    f.text("small", "小字与相似数字仅为辨识测试：0O、1I、8B。", 55, 340, 8)
    f.footer("61")
    data = rasterize(f, f.save(), pages={1}, degraded=True)
    return policy(data, "低清灰度扫描：小字、相似数字和重复金额", ocr="mac",
                  min_native=0, min_ocr=.25)


def hybrid(root):
    f = Fixture(root/"hybrid.pdf", "原生与扫描混合样本")
    for i in range(2):
        f.text(f"title-{i}", "债权材料核对单（自制混合样本）", 50, 755, 17)
        f.text(f"note-{i}", "本页保留同一款项的核对记录。", 55, 660, 13)
        f.text(f"money-{i}", "重复测试金额30,000.00元。", 55, 590, 13)
        f.text(f"id-{i}", f"测试记录HX-{i+1:02}，不得据此认定真实债权。", 55, 520, 12)
        f.footer(str(71+i))
        if i == 0:
            f.next_page()
    data = rasterize(f, f.save(), pages={2})
    return policy(data, "混合PDF：原生文字页与扫描页、跨来源重复金额", ocr="mac",
                  min_native=1, min_ocr=.6)


def additional(root):
    return [factory(root) for factory in (creditors, creditors_merged, table_three_pages,
            table_no_header, page_labels, scan_contract, scan_degraded, hybrid)]
