"""改前/改后对照：同样 6 个真实问题，旧向量召回 vs 新站内检索（本地生产快照库，不发外部请求）"""
import io
import json
import os

os.environ["USE_SQLITE_PROD"] = "true"
os.environ["USE_DEMO_DATA"] = "false"

from app.db.database import SessionLocal  # noqa: E402
from app.ai_engine import graphrag_engine, rag_store  # noqa: E402
from app.ai_engine.retrieval import retrieve  # noqa: E402

QUESTIONS = [
    "马面裙和百褶裙有什么区别？",
    "唐代女子日常穿什么？",
    "香云纱是什么面料？",
    "宋代褙子的形制是怎样的？",
    "团花纹的寓意是什么？",
    "定陵出土了哪些服饰？",
]

prompts = {}


def fake_chat(messages, *a, **k):
    prompts["last"] = messages[-1]["content"]
    return "（占位回答）"


graphrag_engine.chat_completion = fake_chat

db = SessionLocal()
rows = []
for q in QUESTIONS:
    old_hits = [h for h in rag_store.vector_search(q, k=4) if h["id"] != "none"]
    graphrag_engine.graphrag_chat(q, db=db)
    prompt = prompts["last"]
    ctx = prompt.split("可参考史料：")[1].split("\n\n请回答")[0].strip() if "可参考史料：" in prompt else ""
    items = retrieve(q, db)
    rows.append({
        "question": q,
        "old_ids": [h["id"] for h in old_hits],
        "old_first": (old_hits[0]["text"][:40] if old_hits else "（空）"),
        "new_items": [{"type": i["type"], "id": i["id"], "title": i["title"],
                       "score": i["score"], "exact": i["exact"]} for i in items],
        "new_ctx_len": len(ctx),
        "new_head": ctx[:120].replace("\n", " ⏎ "),
    })
db.close()

io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt_before_after.json"),
        "w", encoding="utf-8").write(
    json.dumps(rows, ensure_ascii=False, indent=2))
print("done")
