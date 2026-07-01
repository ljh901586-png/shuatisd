import streamlit as st
import json
import os

# ===================== 常量定义 =====================
DB_FILE = 'maogai_db.json'
ERROR_BOOK_FILE = 'error_book.json'
PROGRESS_FILE = 'progress.json'
PAGE_QUIZ = "quiz"
PAGE_ERROR_BOOK = "error_book"
STATUS_MANUAL = "手动收藏"
STATUS_WRONG = "待重做"
STATUS_FINISH = "已重做答对"
ALL_TAG = "全部题目"

# --- 页面基础配置 ---
st.set_page_config(page_title="智能毛概刷题神器 (Pro Max)", page_icon="📖", layout="centered")

# ===================== 工具函数 =====================
def safe_load_json(file_path, default):
    """安全读取json，损坏/不存在返回默认值"""
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        st.toast(f"文件{file_path}损坏，已重置", icon="⚠️")
        return default

def safe_save_json(file_path, data):
    """安全写入json"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_progress(bank_name):
    data = safe_load_json(PROGRESS_FILE, {})
    return data.get(bank_name, 0)

def save_progress(idx, bank_name):
    data = safe_load_json(PROGRESS_FILE, {})
    data[bank_name] = idx
    safe_save_json(PROGRESS_FILE, data)

@st.cache_data
def load_questions():
    return safe_load_json(DB_FILE, [])

def load_error_book():
    return safe_load_json(ERROR_BOOK_FILE, {})

def save_error_book(data):
    safe_save_json(ERROR_BOOK_FILE, data)

def get_all_tags(question_list):
    """提取所有标签，去重"""
    tags = [ALL_TAG]
    for q in question_list:
        for t in q.get("tags", []):
            if t not in tags:
                tags.append(t)
    return tags

# ===================== 状态初始化 =====================
all_questions = load_questions()
if not all_questions:
    st.error(f"找不到题库文件 {DB_FILE}，请确保它在同一目录下！")
    st.stop()

if "error_book" not in st.session_state:
    st.session_state.error_book = load_error_book()
if "current_idx" not in st.session_state:
    st.session_state.current_idx = load_progress(ALL_TAG)
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "current_page" not in st.session_state:
    st.session_state.current_page = PAGE_QUIZ
if "current_bank" not in st.session_state:
    st.session_state.current_bank = ALL_TAG

# ===================== 侧边栏 =====================
with st.sidebar:
    st.header("🎯 题库选择")
    all_tags = get_all_tags(all_questions)
    selected_bank = st.selectbox("选择当前要刷的题库：", all_tags)

    # 切换题库逻辑
    if st.session_state.current_bank != selected_bank:
        # 清空历史勾选框
        del_keys = [k for k in st.session_state if k.startswith("quiz_opt_")]
        for k in del_keys:
            del st.session_state[k]
        # 更新状态
        st.session_state.current_bank = selected_bank
        st.session_state.current_idx = load_progress(selected_bank)
        st.session_state.submitted = False
        st.rerun()

    st.markdown("---")
    st.header("⚙️ 导航与统计")
    error_count = len(st.session_state.error_book)
    st.metric(label="当前错题总数", value=f"{error_count} 题")

    # 页面切换按钮
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("📖 刷题页面", use_container_width=True, type="primary" if st.session_state.current_page == PAGE_QUIZ else "secondary"):
            st.session_state.current_page = PAGE_QUIZ
            st.rerun()
    with col_s2:
        if st.button("📁 错题本", use_container_width=True, type="primary" if st.session_state.current_page == PAGE_ERROR_BOOK else "secondary"):
            st.session_state.current_page = PAGE_ERROR_BOOK
            st.rerun()

# ===================== 页面1：刷题页 =====================
if st.session_state.current_page == PAGE_QUIZ:
    st.title("📚 智能刷题神器")
    # 筛选当前题库题目
    if st.session_state.current_bank == ALL_TAG:
        current_questions = all_questions
    else:
        current_questions = [q for q in all_questions if st.session_state.current_bank in q.get("tags", [])]
    total_q = len(current_questions)

    if total_q == 0:
        st.warning("⚠️ 当前分类下没有题目，请重新选择！")
    else:
        # 边界保护
        if st.session_state.current_idx >= total_q:
            st.session_state.current_idx = 0
        q = current_questions[st.session_state.current_idx]
        q_id_str = str(q["id"])

        st.progress((st.session_state.current_idx + 1) / total_q)
        st.caption(f"当前进度: {st.session_state.current_idx + 1} / {total_q} | 题号 ID: {q_id_str} | 当前题库: {st.session_state.current_bank}")
        st.markdown(f"### {q['question']}")

        # 渲染选项
        user_check_keys = []
        for opt_letter, opt_text in q["options"].items():
            key = f"quiz_opt_{q_id_str}_{opt_letter}"
            user_check_keys.append(key)
            st.checkbox(f"**{opt_letter}**. {opt_text}", key=key, disabled=st.session_state.submitted)

        st.markdown("---")
        col1, col2 = st.columns(2)

        # 提交/下一题
        with col1:
            if not st.session_state.submitted:
                if st.button("✅ 提交答案", use_container_width=True, type="primary"):
                    st.session_state.submitted = True
                    st.rerun()
            else:
                if st.button("⏭️ 下一题", use_container_width=True, type="primary"):
                    st.session_state.submitted = False
                    # 更新下标
                    if st.session_state.current_idx < total_q - 1:
                        st.session_state.current_idx += 1
                    # 无论是否最后一题都保存进度
                    save_progress(st.session_state.current_idx, st.session_state.current_bank)
                    if st.session_state.current_idx == total_q - 1:
                        st.balloons()
                        st.toast("🎉 本套分类题目已全部刷完！")
                    st.rerun()

        # 加入错题本
        with col2:
            if q_id_str in st.session_state.error_book:
                st.button("⭐ 已在错题本", use_container_width=True, disabled=True)
            else:
                if st.button("⭐ 加入错题本", use_container_width=True):
                    st.session_state.error_book[q_id_str] = {"user_ans": [], "status": STATUS_MANUAL}
                    save_error_book(st.session_state.error_book)
                    st.toast('✅ 成功加入本地错题本！', icon='⭐')
                    st.rerun()

        # 判分逻辑
        if st.session_state.submitted:
            correct_ans = set(q["answer"])
            user_ans = set([opt for opt in q["options"].keys() if st.session_state.get(f"quiz_opt_{q_id_str}_{opt}", False)])
            if not user_ans:
                st.warning("⚠️ 提示：未选择任何选项！")
                st.session_state.submitted = False
                st.rerun()

            correct_str = "".join(sorted(correct_ans))
            user_str = "".join(sorted(user_ans))

            if user_ans == correct_ans:
                st.success(f"🎉 回答正确！")
                # 手动收藏/自动错题统一更新状态
                if q_id_str in st.session_state.error_book:
                    st.session_state.error_book[q_id_str]["status"] = STATUS_FINISH
                    save_error_book(st.session_state.error_book)
            else:
                st.error(f"❌ 回答错误。正确答案是【{correct_str}】，你的选择是【{user_str}】")
                # 自动存入错题
                if q_id_str not in st.session_state.error_book:
                    st.session_state.error_book[q_id_str] = {"user_ans": list(user_ans), "status": STATUS_WRONG}
                    save_error_book(st.session_state.error_book)
                    st.toast('⚠️ 答错啦，已自动存入错题本！', icon='📝')

            # 解析默认收起
            with st.expander("💡 查看详细解析", expanded=False):
                st.info(q.get("explanation", "系统暂无解析。"))

# ===================== 页面2：错题本 =====================
elif st.session_state.current_page == PAGE_ERROR_BOOK:
    st.title("📁 专属错题复盘本")
    error_book = st.session_state.error_book
    if not error_book:
        st.info("🎈 暂无错题，快去刷题收藏错题吧！")
    else:
        # 匹配错题完整题目
        error_questions = [q for q in all_questions if str(q["id"]) in error_book]
        # 标签筛选
        tag_set = set([ALL_TAG])
        for q in error_questions:
            for t in q.get("tags", []):
                tag_set.add(t)
        selected_tag = st.selectbox("🎯 按知识点筛选", list(tag_set))
        if selected_tag != ALL_TAG:
            error_questions = [q for q in error_questions if selected_tag in q.get("tags", [])]

        if len(error_questions) == 0:
            st.info("当前筛选条件下没有匹配错题，请更换筛选标签！")
        else:
            st.write(f"当前筛选下共有 **{len(error_questions)}** 道错题：")
            for idx, q in enumerate(error_questions):
                q_id_str = str(q["id"])
                record = error_book[q_id_str]
                with st.container(border=True):
                    st.markdown(f"**{idx + 1}. {q['question']}**")
                    # 选项展示
                    for opt_letter, opt_text in q["options"].items():
                        st.write(f"{opt_letter}. {opt_text}")
                    # 作答记录
                    status_color = "green" if record["status"] == STATUS_FINISH else "red"
                    user_ans_text = "未记录" if len(record["user_ans"]) == 0 else "".join(sorted(record["user_ans"]))
                    st.markdown(f"> ✅ **正确答案**: `{''.join(sorted(q['answer']))}` &nbsp;&nbsp;|&nbsp;&nbsp; ❌ **你上次选了**: `{user_ans_text}` &nbsp;&nbsp;|&nbsp;&nbsp; 📌 **状态**: <span style='color:{status_color}'>{record['status']}</span>", unsafe_allow_html=True)
                    # 操作按钮
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        if st.button("🔄 重做本题", key=f"redo_{q_id_str}", use_container_width=True):
                            # 定位题目原始索引，不强制切全部题目
                            target_idx = next((i for i, item in enumerate(all_questions) if item["id"] == q["id"]), 0)
                            # 切换回全部题目，保留原逻辑
                            st.session_state.current_bank = ALL_TAG
                            st.session_state.current_idx = target_idx
                            save_progress(target_idx, ALL_TAG)
                            st.session_state.submitted = False
                            st.session_state.current_page = PAGE_QUIZ
                            st.rerun()
                    with c2:
                        if st.button("🗑️ 移出错题本", key=f"remove_{q_id_str}", use_container_width=True):
                            del st.session_state.error_book[q_id_str]
                            save_error_book(st.session_state.error_book)
                            st.toast("✅ 已从错题本移除！")
                            st.rerun()
                st.divider()

        # 清空全部错题 增加二次确认弹窗
        st.markdown("---")
        with st.expander("⚠️ 危险操作：清空全部错题"):
            st.warning("清空后无法恢复，确定要删除所有错题记录吗？")
            confirm = st.checkbox("我确认要清空全部错题，不可恢复")
            if confirm and st.button("💥 确认全部清空", type="primary"):
                st.session_state.error_book = {}
                save_error_book({})
                st.toast("🧹 错题本已彻底清空！")
                st.rerun()