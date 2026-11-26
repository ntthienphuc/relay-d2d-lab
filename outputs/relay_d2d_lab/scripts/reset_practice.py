"""Archive only non-reference run folders after all dashboards have closed."""
import json
import re
import socket
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def archive_runs(results, archives):
    evidence = set(json.loads((results / "final/evidence_ids.json").read_text(encoding="utf-8")))
    candidates = []
    for folder in sorted(results.iterdir()):
        match = re.fullmatch(r"run_(\d+)", folder.name)
        if (match and int(match[1]) not in evidence and folder.is_dir()
                and folder.resolve().parent == results.resolve() and not folder.is_symlink()):
            candidates.append(folder)
    if not candidates:
        return None, 0
    destination = archives / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destination.mkdir(parents=True)
    for folder in candidates:
        folder.rename(destination / folder.name)
    return destination, len(candidates)

def main():
    for port in (8765, 8877):
        with socket.socket() as check:
            check.settimeout(0.5)
            if check.connect_ex(("127.0.0.1", port)) == 0:
                print(f"Hãy đóng dashboard đang chạy ở cổng {port}, rồi thử lại.")
                return 1
    folder, count = archive_runs(ROOT / "results", ROOT / ".luu_phien")
    print(f"Đã cất {count} lượt đo vào {folder}" if count else "Danh sách lượt mới đang trống.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

