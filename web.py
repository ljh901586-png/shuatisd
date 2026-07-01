import streamlit as st
import json
import random

# --- 页面基本设置 ---
st.set_page_config(page_title="智能毛概刷题神器", page_icon="📖", layout="centered")

# --- 加载题库数据 ---
@st.cache_data
def load_data():
    try:
        with open('maogai_db.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("找不到 maogai_db.json 题库文件，请确保它和本代码在同一目录下！")
        return []

all_questions = load_data()

if not all_questions:
    st.stop()

# --- 初始化 Session State (状态记忆) ---
# Streamlit 每次点击按钮都会重新运行代码，所以必须用 session_state 记住当前做到哪题了
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'error_book' not in st.session_state:
    st.session_state.error_book = set()

# --- 侧边栏设置 ---
with st.sidebar:
    st.header("⚙️ 刷题设置")
    
    # 提取所有标签
    all_tags = set(["全部标签"])
    for q in all_questions:
        for t in q.get("tags", []):
            all_tags.add(t)
            
    selected_tag = st.selectbox("选择知识点", list(all_tags))
    
    st.markdown("---")
    st.metric(label="错题本数量", value=f"{len(st.session_state.error_book)} 题")
    if st.button("清空错题本"):
        st.session_state.error_book = set()
        st.success("错题本已清空！")

# --- 过滤题目池 ---
if selected_tag == "全部标签":
    pool = all_questions
else:
    pool = [q for q in all_questions if selected_tag in q.get("tags", [])]

total_q = len(pool)

if total_q == 0:
    st.warning("当前标签下没有题目！")
    st.stop()

# 安全处理越界
if st.session_state.current_idx >= total_q:
    st.session_state.current_idx = 0

# --- 主界面：展示当前题目 ---
q = pool[st.session_state.current_idx]

st.title("📚 毛概多选题刷题神器")
st.progress((st.session_state.current_idx + 1) / total_q)
st.caption(f"当前进度: {st.session_state.current_idx + 1} / {total_q} | 题号 ID: {q['id']}")

st.markdown(f"### {q['question']}")

# 选项展示 (使用多选框)
for opt_letter, opt_text in q['options'].items():
    # 动态生成复选框，并通过 key 绑定状态
    st.checkbox(
        f"**{opt_letter}**. {opt_text}", 
        key=f"opt_{q['id']}_{opt_letter}",
        disabled=st.session_state.submitted
    )

st.markdown("---")

# --- 底部按钮逻辑 ---
col1, col2 = st.columns(2)

with col1:
    if not st.session_state.submitted:
        if st.button("✅ 提交答案", use_container_width=True, type="primary"):
            st.session_state.submitted = True
            st.rerun()
    else:
        if st.button("⏭️ 下一题", use_container_width=True, type="primary"):
            st.session_state.submitted = False
            if st.session_state.current_idx < total_q - 1:
                st.session_state.current_idx += 1
            else:
                st.balloons()
                st.success("恭喜你！本组题目已全部刷完！")
            st.rerun()

with col2:
    if st.button("⭐ 加入错题本", use_container_width=True):
        st.session_state.error_book.add(q['id'])
        st.toast('已成功加入错题本！', icon='⭐')

# --- 判分与解析展示 ---
if st.session_state.submitted:
    correct_ans = set(q['answer'])
    # 获取用户勾选了哪些
    user_ans = set()
    for opt in q['options'].keys():
        if st.session_state.get(f"opt_{q['id']}_{opt}", False):
            user_ans.add(opt)
            
    if not user_ans:
        st.warning("⚠️ 你还没有选择任何选项哦！")
        st.session_state.submitted = False
        st.rerun()
        
    correct_str = "".join(sorted(correct_ans))
    user_str = "".join(sorted(user_ans))
    
    if user_ans == correct_ans:
        st.success(f"🎉 回答正确！")
    else:
        st.error(f"❌ 回答错误。正确答案是【{correct_str}】，你的选择是【{user_str}】")
        # 自动加入错题本
        st.session_state.error_book.add(q['id'])
        
    with st.expander("💡 查看详细解析", expanded=True):
        st.info(q.get('explanation', "系统暂无解析。"))