import streamlit as st
from manual_qa_helper import load_manual_from_bytes, search_qa, llm_answer

st.set_page_config(page_title="最小RAG文档问答", layout="wide")

# ========== 顶部标题说明 ==========
st.title("📄 最小RAG｜DeepSeek文档问答助手")
st.markdown("""
> 功能说明：上传PDF手册 → 自动分片检索 → AI基于原文回答
> ⚠️ 规则：只使用文档内信息，找不到内容会直接提示
""")

# ========== 侧边栏参数 ==========
with st.sidebar:
    st.header("⚙️ 参数设置")
    chunk_size = st.slider("分片长度", min_value=200, max_value=1000, value=500, step=50)
    overlap = st.slider("分片重叠", min_value=20, max_value=200, value=80, step=10)
    top_num = st.slider("最多取几条参考片段", min_value=1, max_value=5, value=3)
    st.divider()
    st.info("API密钥在Streamlit后台Secrets配置，不要写在代码里")
    if st.button("清空已加载文档"):
        st.session_state.pop("chunks", None)
        st.success("文档缓存已清空")

# ========== 上传区 ==========
uploaded_file = st.file_uploader("📂 上传PDF手册", type="pdf")
if uploaded_file is not None:
    with st.spinner("正在读取、拆分文档分片..."):
        chunks = load_manual_from_bytes(uploaded_file, chunk_size, overlap)
        st.session_state["chunks"] = chunks
    st.success(f"✅ 文档加载完成，一共拆分 {len(chunks)} 个文本分片")

# ========== 问答区 ==========
question = st.text_input("💬 输入你的问题")
ask_btn = st.button("开始查询")

if ask_btn and question.strip():
    if "chunks" not in st.session_state:
        st.warning("请先上传PDF文档！")
    else:
        with st.spinner("检索+调用DeepSeek..."):
            hit_list = search_qa(st.session_state["chunks"], question)
            hit_list = hit_list[:top_num]
            if not hit_list:
                answer = "文档中没有找到相关内容。"
            else:
                ctx = "\n".join([i["text"] for i in hit_list])
                api_key = ""
                if not api_key:
                    answer = "⚠️ 未配置DeepSeek密钥，仅展示检索原文"
                else:
                    answer = llm_answer(question, ctx, api_key)
        # 展示结果
        st.subheader("✅ 回答结果")
        st.write(answer)
        st.subheader("📜 原文依据段落")
        for idx, item in enumerate(hit_list):
            with st.expander(f"段落{idx+1}，命中关键词：{item['hit']}"):
                st.write(item["text"])
        # 下载按钮
        download_text = f"问题：{question}\n回答：{answer}\n\n=====参考原文=====\n" + "\n".join([i["text"] for i in hit_list])
        st.download_button("📥 下载本次问答结果(txt)", data=download_text, file_name="问答结果.txt")
