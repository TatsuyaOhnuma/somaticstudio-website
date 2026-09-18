#!/usr/bin/env python3
"""週次JSONを唯一の情報源として、投稿スケジュールCSVと撮影台本Markdownを生成する。

  python3 build.py

出力:
  schedule.csv        … Manus / Meta Business Suite へ流し込む予約投稿データ
  scripts/week-NN.md  … 撮影・編集用の台本シート
"""
import csv, glob, json, os
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
WD_JA = ["月", "火", "水", "木", "金", "土", "日"]
PILLAR_LABEL = {
    "core": "이완 프로토콜", "science": "몸의 과학", "pain": "증상별 처방",
    "mind": "마음과 몸", "myth": "오해를 깬다", "sense": "감각 훈련",
    "philosophy": "철학·에세이",
}
# 曜日(0=月)ごとに来るべき pillar。ズレは構成ミスなので検証で弾く。
PILLAR_BY_WEEKDAY = ["core", "science", "pain", "mind", "myth", "sense", "philosophy"]


def load():
    cfg = json.load(open(os.path.join(ROOT, "data/config.json"), encoding="utf-8"))
    tags = json.load(open(os.path.join(ROOT, "data/hashtags.json"), encoding="utf-8"))
    weeks = [json.load(open(p, encoding="utf-8"))
             for p in sorted(glob.glob(os.path.join(ROOT, "data/week-*.json")))]
    return cfg, tags, weeks


def hashtags_for(tags, pillar):
    return " ".join(tags["common"] + tags["sets"][pillar])


def validate(cfg, weeks):
    errors = []
    seen_no, seen_date = set(), set()
    for w in weeks:
        for r in w["reels"]:
            d = date.fromisoformat(r["date"])
            if r["no"] in seen_no:
                errors.append(f"#{r['no']}: 番号が重複")
            if r["date"] in seen_date:
                errors.append(f"{r['date']}: 日付が重複")
            seen_no.add(r["no"])
            seen_date.add(r["date"])
            if PILLAR_BY_WEEKDAY[d.weekday()] != r["pillar"]:
                errors.append(f"#{r['no']} {r['date']}: 曜日と柱が不一致 "
                              f"({r['pillar']} / 期待={PILLAR_BY_WEEKDAY[d.weekday()]})")
            for key in ("title", "hook", "script", "caption", "cta", "shots"):
                if not r.get(key):
                    errors.append(f"#{r['no']}: {key} が空")
    if len(seen_no) != cfg["total_posts"]:
        errors.append(f"本数が {len(seen_no)} 件（想定 {cfg['total_posts']} 件）")
    return errors


def full_caption(r, tags):
    parts = [r["caption"], r["cta"], hashtags_for(tags, r["pillar"])]
    return "\n\n".join(parts)


def build_csv(cfg, tags, weeks):
    path = os.path.join(ROOT, "schedule.csv")
    cols = ["no", "date", "weekday", "time", "timezone", "week", "pillar", "pillar_label",
            "title", "hook", "duration_sec", "caption_full", "caption", "cta", "hashtags",
            "script_file", "media_file", "status"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for wk in weeks:
            for r in wk["reels"]:
                d = date.fromisoformat(r["date"])
                w.writerow({
                    "no": r["no"], "date": r["date"], "weekday": WD_JA[d.weekday()],
                    "time": cfg["post_time"], "timezone": cfg["timezone"],
                    "week": wk["week"], "pillar": r["pillar"],
                    "pillar_label": PILLAR_LABEL[r["pillar"]],
                    "title": r["title"], "hook": r["hook"], "duration_sec": r["duration"],
                    "caption_full": full_caption(r, tags),
                    "caption": r["caption"], "cta": r["cta"],
                    "hashtags": hashtags_for(tags, r["pillar"]),
                    "script_file": f"scripts/week-{wk['week']:02d}.md",
                    "media_file": f"reel-{r['no']:03d}.mp4", "status": "未撮影",
                })
    return path


def build_scripts(cfg, tags, weeks):
    outdir = os.path.join(ROOT, "scripts")
    os.makedirs(outdir, exist_ok=True)
    written = []
    for wk in weeks:
        lines = [f"# Week {wk['week']:02d} — {wk['theme']}", ""]
        first, last = wk["reels"][0]["date"], wk["reels"][-1]["date"]
        lines += [f"配信期間: {first} 〜 {last}　/　投稿時刻: {cfg['post_time']} ({cfg['timezone']})", ""]
        for r in wk["reels"]:
            d = date.fromisoformat(r["date"])
            lines += [
                "---", "",
                f"## #{r['no']:03d}　{r['date']} ({WD_JA[d.weekday()]})　{PILLAR_LABEL[r['pillar']]}",
                "", f"**{r['title']}**　/　目安 {r['duration']}秒　/　素材名 `reel-{r['no']:03d}.mp4`", "",
                "### フック（冒頭1.5秒）", "", f"> {r['hook']}", "",
                "### 画面テロップ", "",
            ]
            lines += [f"{i}. {t}" for i, t in enumerate(r["onscreen"], 1)]
            lines += ["", "### 台本（読み上げ）", ""]
            lines += [f"{ln}  " for ln in r["script"].split("\n")]
            lines += ["", "### 撮影メモ", "", r["shots"], "", "### キャプション（投稿用・全文）", "", "```"]
            lines += full_caption(r, tags).split("\n")
            lines += ["```", ""]
        path = os.path.join(outdir, f"week-{wk['week']:02d}.md")
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        written.append(path)
    return written


def main():
    cfg, tags, weeks = load()
    errors = validate(cfg, weeks)
    if errors:
        print("検証エラー:")
        for e in errors:
            print("  -", e)
        raise SystemExit(1)
    csv_path = build_csv(cfg, tags, weeks)
    scripts = build_scripts(cfg, tags, weeks)
    total = sum(len(w["reels"]) for w in weeks)
    print(f"OK  {total}本 / {len(weeks)}週")
    print(f"  {os.path.relpath(csv_path, ROOT)}")
    print(f"  scripts/ に {len(scripts)} ファイル")


if __name__ == "__main__":
    main()
