"""Explicit download step for public, free model weights and an OFL Chinese font.

This script accepts no documents, account tokens, or API keys. Runtime conversion
never invokes it. curl uses system TLS trust; certificate checks stay enabled.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = [
    ("docling-project/docling-layout-heron", "8f39ad3c0b4c58e9c2d2c84a38465abf757272d8",
     ["config.json", "preprocessor_config.json", "model.safetensors", "README.md"]),
    ("docling-project/docling-models", "fc0f2d45e2218ea24bce5045f58a389aed16dc23",
     ["README.md", "model_artifacts/tableformer/accurate/tm_config.json",
      "model_artifacts/tableformer/accurate/tableformer_accurate.safetensors"]),
]


def download(url: str, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        return
    temp = target.with_suffix(target.suffix+".part")
    subprocess.run(["curl", "--disable", "--fail", "--location", "--silent", "--show-error",
                    "--retry", "2", "--max-time", "600", url, "-o", str(temp)], check=True)
    temp.replace(target)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    lock = {"schema_version": 1, "models": [], "files": []}
    for repo, revision, files in MODELS:
        print(f"准备公开模型：{repo}@{revision}", flush=True)
        lock["models"].append({"repo": repo, "revision": revision})
        for name in files:
            path = ROOT / ".cache/models" / repo.replace("/", "--") / name
            download(f"https://huggingface.co/{repo}/resolve/{revision}/{name}", path)
            lock["files"].append({"path": str(path.relative_to(ROOT/".cache/models")),
                                  "sha256": sha256(path), "bytes": path.stat().st_size})
    path = ROOT / ".cache/models/manifest.json"
    # Record the observed lock separately; compare it on subsequent preparation.
    expected = ROOT / "models.lock.json"
    if expected.exists() and json.loads(expected.read_text()) != lock:
        raise SystemExit("模型文件与 models.lock.json 不一致；拒绝静默更新锁文件")
    if not expected.exists():
        expected.write_text(json.dumps(lock, indent=2)+"\n")
    path.write_text(json.dumps(lock, indent=2)+"\n")
    font_revision = "47d54ca1ebb14fd864695f1d39dc734f39017c33"
    download(f"https://raw.githubusercontent.com/google/fonts/{font_revision}/ofl/notosanssc/"
             "NotoSansSC%5Bwght%5D.ttf", ROOT/".cache/fonts/NotoSansSC.ttf")
    download(f"https://raw.githubusercontent.com/google/fonts/{font_revision}/ofl/notosanssc/OFL.txt",
             ROOT/"third_party/NotoSansSC-OFL.txt")
    font_lock = ROOT/"font.lock.json"
    if font_lock.is_file():
        expected_font = json.loads(font_lock.read_text())["sha256"]
        if sha256(ROOT/".cache/fonts/NotoSansSC.ttf") != expected_font:
            raise SystemExit("字体与 font.lock.json 不一致；拒绝继续生成样本")
    print("公开资源准备完成；转换与核对不再下载资源。", flush=True)


if __name__ == "__main__":
    main()
