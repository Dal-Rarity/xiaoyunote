"""
Recall@5 评测（区分精确题和开放题）
- 精确题：expect_article_ids 有值 → 按 ID 命中计算
- 开放题：expect_article_ids 为空且非拒答题 → 判断是否召回了真实文章
"""
import asyncio
import csv
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from ai_app.services.retriever import retrieve

CSV_PATH = os.path.join(BASE_DIR, "data", "eval", "eval-cases-v1.csv")
TOP_K = 5

# 开放题：无标准答案，只判断"是否召回了文章"
OPEN_QUESTIONS = {"6", "7", "10"}


async def main():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    exact_hits = 0
    exact_total = 0
    open_hits = 0
    open_total = 0
    details = []

    for row in rows:
        qid = row["id"]
        q = row["question"]
        user_id = int(row.get("user_id") or 1)
        expect_raw = (row.get("expect_article_ids") or "").strip()

        r = await retrieve(q, user_id=user_id)

        if qid in OPEN_QUESTIONS:
            # 开放题：只要召回真实文章就算命中
            hit = (not r.refused) and len(r.chunks) > 0
            open_total += 1
            open_hits += int(hit)
            details.append(("OPEN", qid, q, "—", [c.article_id for c in r.chunks], hit))
        elif expect_raw:
            # 精确题：按 ID 命中
            expect = set(int(x) for x in expect_raw.split("|") if x.strip())
            got = {c.article_id for c in r.chunks[:TOP_K]}
            hit = bool(expect & got)
            exact_total += 1
            exact_hits += int(hit)
            details.append(("EXACT", qid, q, sorted(expect), sorted(got), hit))
        else:
            # 无关/边界题：看是否正确拒答
            hit = r.refused
            details.append(("SAFE", qid, q, "拒答", "拒答" if r.refused else f"回答({len(r.chunks)}条)", hit))

    print(f"\n=== 精确题 Recall@{TOP_K} = {exact_hits}/{exact_total} = "
          f"{exact_hits/exact_total if exact_total else 0:.4f} ===")
    print(f"=== 开放题命中率 = {open_hits}/{open_total} = "
          f"{open_hits/open_total if open_total else 0:.4f} ===\n")

    for kind, qid, q, expect, got, hit in details:
        mark = "OK  " if hit else "MISS"
        print(f"[{mark}] [{kind}] Q{qid}: {q}")
        print(f"    expect={expect}  got={got}")


if __name__ == "__main__":
    asyncio.run(main())