import streamlit as st
import json
import os

# --- 页面基本设置 ---
st.set_page_config(page_title="智能毛概刷题神器 (Pro Max)", page_icon="📖", layout="centered")

# --- 核心文件路径 ---
DB_FILE = 'maogai_db.json'
ERROR_BOOK_FILE = 'error_book.json'

# --- 数据加载与持久化逻辑 ---
@st.cache_data
def load_questions():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_error_book():
    """读取本地错题本文件"""
    if os.path.exists(ERROR_BOOK_FILE):
        with open(ERROR_BOOK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {} # 格式: {"题目ID": {"user_ans": ["A", "B"], "status": "待重做"}}

def save_error_book(data):
    """持久化保存错题本到本地"""
    with open(ERROR_BOOK_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 初始化状态 ---
all_questions = load_questions()
if not all_questions:
    st.error(f"找不到题库文件 {DB_FILE}，请确保它在同一目录下！")
    st.stop()

if 'error_book' not in st.session_state:
    st.session_state.error_book = load_error_book()
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'quiz' # 'quiz' 刷题页, 'error_book' 错题本页

# --- 侧边栏：全局导航与实时统计 ---
with st.sidebar:
    st.header("⚙️ 导航与统计")
    
    # 实时统计
    error_count = len(st.session_state.error_book)
    st.metric(label="当前错题总数", value=f"{error_count} 题")
    
    # 页面切换
    st.markdown("---")
    if st.button("📝 返回刷题主页", use_container_width=True, type="primary" if st.session_state.current_page == 'quiz' else "secondary"):
        st.session_state.current_page = 'quiz'
        st.rerun()
        
    if st.button("📁 查看全部错题", use_container_width=True, type="primary" if st.session_state.current_page == 'error_book' else "secondary"):
        st.session_state.current_page = 'error_book'
        st.rerun()

# ==========================================
# 页面一：刷题模式
# ==========================================
if st.session_state.current_page == 'quiz':
    st.title("📚 毛概多选题刷题")
    
    total_q = len(all_questions)
    q = all_questions[st.session_state.current_idx]
    q_id_str = str(q['id'])
    
    st.progress((st.session_state.current_idx + 1) / total_q)
    st.caption(f"当前进度: {st.session_state.current_idx + 1} / {total_q} | 题号 ID: {q_id_str}")
    st.markdown(f"### {q['question']}")

    # 选项展示
    for opt_letter, opt_text in q['options'].items():
        st.checkbox(f"**{opt_letter}**. {opt_text}", key=f"quiz_opt_{q_id_str}_{opt_letter}", disabled=st.session_state.submitted)

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    # 【提交与下一题逻辑】
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
                    st.toast("🎉 本套题目已全部刷完！")
                st.rerun()
                
    # 【加入错题本按钮交互优化】
    with col2:
        if q_id_str in st.session_state.error_book:
            st.button("⭐ 已在错题本", use_container_width=True, disabled=True)
        else:
            if st.button("⭐ 加入错题本", use_container_width=True):
                st.session_state.error_book[q_id_str] = {"user_ans": [], "status": "手动收藏"}
                save_error_book(st.session_state.error_book)
                st.toast('✅ 成功加入本地错题本！', icon='⭐')
                st.rerun()

    # 【判分与自动加入错题本逻辑】
    if st.session_state.submitted:
        correct_ans = set(q['answer'])
        user_ans = set([opt for opt in q['options'].keys() if st.session_state.get(f"quiz_opt_{q_id_str}_{opt}", False)])
            
        if not user_ans:
            st.warning("⚠️ 提示：未选择任何选项！")
            st.session_state.submitted = False
            st.rerun()
            
        correct_str = "".join(sorted(correct_ans))
        user_str = "".join(sorted(user_ans))
        
        if user_ans == correct_ans:
            st.success(f"🎉 回答正确！")
            # 如果这道题原来在错题本里，标记为已重做完成
            if q_id_str in st.session_state.error_book:
                st.session_state.error_book[q_id_str]["status"] = "已重做答对"
                save_error_book(st.session_state.error_book)
        else:
            st.error(f"❌ 回答错误。正确答案是【{correct_str}】，你的选择是【{user_str}】")
            # 自动错题录入逻辑
            if q_id_str not in st.session_state.error_book:
                st.session_state.error_book[q_id_str] = {"user_ans": list(user_ans), "status": "待重做"}
                save_error_book(st.session_state.error_book)
                st.toast('⚠️ 答错啦，已自动存入错题本！', icon='📝')
            
        with st.expander("💡 查看详细解析", expanded=True):
            st.info(q.get('explanation', "系统暂无解析。"))

# ==========================================
# 页面二：专属错题本复盘
# ==========================================
elif st.session_state.current_page == 'error_book':
    st.title("📁 专属错题复盘本")
    
    if not st.session_state.error_book:
        st.info("🎈 暂无错题，快去刷题收藏错题吧！")
    else:
        # 提取错题本中的详细题目数据
        error_questions = [q for q in all_questions if str(q['id']) in st.session_state.error_book]
        
        # 知识点标签筛选
        all_tags = set(["全部错题"])
        for q in error_questions:
            for t in q.get("tags", []): all_tags.add(t)
        selected_tag = st.selectbox("🎯 按知识点筛选", list(all_tags))
        
        if selected_tag != "全部错题":
            error_questions = [q for q in error_questions if selected_tag in q.get("tags", [])]
        
        st.write(f"当前筛选下共有 **{len(error_questions)}** 道错题：")
        
        # 遍历展示错题
        for idx, q in enumerate(error_questions):
            q_id_str = str(q['id'])
            record = st.session_state.error_book[q_id_str]
            
            with st.container():
                st.markdown(f"**{idx + 1}. {q['question']}**")
                
                # 展示选项
                for opt_letter, opt_text in q['options'].items():
                    st.write(f"{opt_letter}. {opt_text}")
                
                # 展示作答记录与状态
                status_color = "green" if record['status'] == "已重做答对" else "red"
                st.markdown(f"> ✅ **正确答案**: `{''.join(sorted(q['answer']))}` &nbsp;&nbsp;|&nbsp;&nbsp; ❌ **你上次选了**: `{''.join(sorted(record['user_ans'])) if record['user_ans'] else '未记录'}` &nbsp;&nbsp;|&nbsp;&nbsp; 📌 **状态**: <span style='color:{status_color}'>{record['status']}</span>", unsafe_allow_html=True)
                
                # 操作按钮
                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.button("🔄 重做本题", key=f"redo_{q_id_str}", use_container_width=True):
                        # 定位到原题库索引
                        original_idx = next((i for i, item in enumerate(all_questions) if item["id"] == q['id']), 0)
                        st.session_state.current_idx = original_idx
                        st.session_state.submitted = False
                        st.session_state.current_page = 'quiz'
                        st.rerun()
                with c2:
                    if st.button("🗑️ 移出错题本", key=f"remove_{q_id_str}", use_container_width=True):
                        del st.session_state.error_book[q_id_str]
                        save_error_book(st.session_state.error_book)
                        st.toast("✅ 已从错题本移除！")
                        st.rerun()
                st.divider()
        
        # 批量清空功能（带防误触展开）
        with st.expander("⚠️ 危险操作：清空全部错题"):
            st.warning("清空后无法恢复，确定要删除错题本里的所有记录吗？")
            if st.button("💥 确认全部清空", type="primary"):
                st.session_state.error_book = {}
                save_error_book({})
                st.toast("🧹 错题本已彻底清空！")
                st.rerun()