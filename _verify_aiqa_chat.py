# -*- coding: utf-8 -*-
"""验证 /aiqa/chat 多轮对话接口（香云纱 + 追问）"""
import urllib.request, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def chat(q, history=None):
    body = json.dumps({"question": q, "history": history or []}).encode('utf-8')
    req = urllib.request.Request('http://47.93.14.11/api/aiqa/chat', data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode('utf-8'))

r1 = chat('香云纱是什么面料？')
print('Q1 香云纱:')
print(r1['answer'][:400])
print('ref:', r1['source_ref'])
print('---')

r2 = chat('它为什么叫“响云纱”？', [{'role':'user','content':'香云纱是什么面料？'},{'role':'assistant','content':r1['answer']}])
print('Q2 追问(带历史):')
print(r2['answer'][:300])
print('ref:', r2['source_ref'])
print('=== DONE ===')
