import requests
from PyPDF2 import PdfReader

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"

def load_manual_from_bytes(pdf_bytes, chunk_size=500, overlap=80):
    reader = PdfReader(pdf_bytes)
    full_text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            full_text += t
    chunks = []
    start = 0
    text_len = len(full_text)
    while start < text_len:
        end = start + chunk_size
        chunk = full_text[start:end]
        chunks.append({"text": chunk, "hit":0})
        start = end - overlap
    return chunks

def search_qa(para_list: list[dict], question: str):
    q_words = question.replace("，"," ").replace("。"," ").split()
    for p in para_list:
        cnt = 0
        for w in q_words:
            if w and w in p["text"]:
                cnt += 1
        p["hit"] = cnt
    res = [p for p in para_list if p["hit"]>0]
    res.sort(key=lambda x:x["hit"], reverse=True)
    return res

def llm_answer(question, context_text, api_key):
    prompt = f"""
你是文档问答助手，请严格根据【参考原文】回答用户问题，不要编造原文不存在的信息。
如果原文没有相关内容，直接回复：文档中没有找到该问题相关信息。
【参考原文】
{context_text}
【用户问题】
{question}
只输出回答，不要多余解释。
"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role":"user","content":prompt}],
        "temperature":0.1
    }
    resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
    j = resp.json()
    if resp.status_code == 200:
        return j["choices"][0]["message"]["content"]
    else:
        return f"调用失败：{j}"
