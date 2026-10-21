"""Reproduce the complete macOS demo in a fresh source copy and empty cache.

Requires an existing Python 3.12, uv, curl and macOS Vision. Installation and
public asset download use the network; PDF processing runs in an OS network sandbox.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="从空源码副本、环境及缓存复现10份自制PDF")
    parser.add_argument("--dest", type=Path, required=True, help="必须尚不存在；保留验证现场")
    parser.add_argument("--python", type=Path, default=Path(sys.base_prefix)/"bin/python3")
    args = parser.parse_args()
    dest = args.dest.resolve()
    if dest.exists():
        parser.error("目标已存在；不会删除或复用，请指定新目录")
    if sys.platform != "darwin" or not Path("/usr/bin/sandbox-exec").is_file():
        parser.error("完整回归目前仅验证macOS，不能跳过OCR或系统网络沙箱冒充通过")
    uv = shutil.which("uv")
    if not uv or not args.python.is_file() or not shutil.which("curl"):
        parser.error("需要已有uv、curl和Python 3.12；不安装系统级工具")
    version = subprocess.check_output(
        [str(args.python), "-c", "import sys;print('.'.join(map(str,sys.version_info[:3])))"],
        text=True,
    ).strip()
    if not version.startswith("3.12."):
        parser.error("需要Python 3.12")
    dest.mkdir(parents=True)
    project, logs = dest/"project", dest/"logs"
    project.mkdir()
    logs.mkdir()
    files = [ROOT/name for name in (
        "pyproject.toml", "uv.lock", "models.lock.json", "font.lock.json", "README.md",
        ".gitignore", "CONTRIBUTING.md", "LICENSE",
    ) if (ROOT/name).is_file()]
    for folder in ("src", "scripts", "tests", "docs", "third_party"):
        files.extend(p for p in (ROOT/folder).rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and p.suffix != ".pyc"
                     and p.name != "prepare_release.py")
    manifest = []
    for source in sorted(files):
        if source.is_symlink():
            raise ValueError("source_symlink_not_allowed")
        relative = source.relative_to(ROOT)
        target = project/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        manifest.append({"path": relative.as_posix(), "sha256": sha(target)})
    assert not any((project/p).exists() for p in (".venv", ".cache", "fixtures", "output", "contrib_review"))
    result = {
        "status": "running", "python_prerequisite": version,
        "platform": {"system": platform.system(), "machine": platform.machine(),
                     "macos": platform.mac_ver()[0]},
        "isolation": {"fresh_source_copy": True, "old_venv_copied": False,
                      "old_uv_cache_reused": False, "old_model_cache_copied": False,
                      "old_fixture_or_output_copied": False,
                      "same_os_vision_and_python_prerequisites": True},
        "source_manifest": manifest, "stages": [],
    }
    report_path = dest/"result.json"

    def save():
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")

    env = os.environ.copy()
    for key in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME", "UV_PROJECT_ENVIRONMENT",
                "UV_CONFIG_FILE", "UV_INDEX", "UV_DEFAULT_INDEX", "PIP_INDEX_URL",
                "PIP_EXTRA_INDEX_URL", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        env.pop(key, None)
    env.update({"PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": str(dest/"uv-cache"),
                "HF_HOME": str(project/".cache/hf"), "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
                "HF_HUB_DISABLE_TELEMETRY": "1"})
    save()

    def run(name, command, *, offline=False):
        start = time.perf_counter()
        print(f"开始：{name}", flush=True)
        stage_env = env.copy()
        if offline:
            stage_env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
            command = ["/usr/bin/sandbox-exec", "-p",
                       "(version 1)(allow default)(deny network*)", *map(str, command)]
        with (logs/f"{name}.log").open("w") as stream:
            outcome = subprocess.run(list(map(str, command)), cwd=project, env=stage_env,
                                     stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
        result["stages"].append({"name": name, "exit_code": outcome.returncode,
                                  "offline_os_sandbox": offline,
                                  "elapsed_seconds": round(time.perf_counter()-start, 3),
                                  "log": f"logs/{name}.log"})
        save()
        if outcome.returncode:
            raise RuntimeError(f"阶段失败：{name}；见 {logs/(name+'.log')}")
        print(f"完成：{name}", flush=True)

    py = project/".venv/bin/python"
    try:
        run("01-install", [uv, "--native-tls", "--no-config", "sync", "--frozen",
            "--no-editable", "--no-python-downloads", "--python", args.python.resolve(),
            "--default-index", "https://pypi.org/simple", "--extra", "dev", "--extra", "ocr-mac"])
        run("02-installed-import", [py, "-c",
            "import cntrace,sys;from pathlib import Path;"
            "p=Path(cntrace.__file__).resolve();print(sys.version);print(p);"
            "assert p.is_relative_to(Path('.venv').resolve())"])
        run("03-public-assets", [py, "scripts/prepare_assets.py"])
        probe = ("import socket,errno\ns=socket.socket()\ntry:\n s.connect(('127.0.0.1',9))\n"
                 "except OSError as e:\n assert e.errno==errno.EPERM,repr(e)\n"
                 " print('OS sandbox rejected socket connection')\nelse:\n"
                 " raise AssertionError('network unexpectedly allowed')\nfinally:\n s.close()")
        run("04-network-denial", [py, "-c", probe], offline=True)
        run("05-generate-fixtures", [py, "scripts/make_fixtures.py"], offline=True)
        generated = json.loads((project/"fixtures/gold.json").read_text())
        first_hashes = {d["pdf"]: sha(project/"fixtures"/d["pdf"]) for d in generated["documents"]}
        assert len(first_hashes) == 10
        first_gold = sha(project/"fixtures/gold.json")
        run("05b-repeat-generation", [py, "scripts/make_fixtures.py"], offline=True)
        assert all(sha(project/"fixtures"/name) == digest for name, digest in first_hashes.items())
        assert sha(project/"fixtures/gold.json") == first_gold
        result["fixture_comparison"] = {
            "fresh_generation_pdf_bytes_repeatable": len(first_hashes),
            "fresh_generation_gold_bytes_repeatable": True,
            "fixture_hashes": first_hashes,
        }
        save()
        run("06-demo", [py, "scripts/run_demo.py"], offline=True)
        run("07-regression", [py, "-m", "pytest", "-c", "pyproject.toml", "--rootdir=.",
            "--confcutdir=.", "-q", "--junitxml=output/regression.xml"], offline=True)
        run("08-acceptance", [py, "scripts/acceptance.py", "--junit", "output/regression.xml",
                               "--out", "output/acceptance.json"], offline=True)
        suites = ET.parse(project/"output/regression.xml").getroot().findall("testsuite")
        result["regression"] = {field: sum(int(s.get(field, "0")) for s in suites)
                                for field in ("tests", "failures", "errors", "skipped")}
        assert result["regression"]["tests"] > 0
        assert not any(result["regression"][field] for field in ("failures", "errors", "skipped"))
        result["status"] = "passed"
        save()
        print(f"从零复现完成：{report_path}", flush=True)
    except Exception as exc:
        result["status"] = "failed"
        result["failure"] = str(exc)
        save()
        raise


if __name__ == "__main__":
    main()
