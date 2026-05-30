import random
import streamlit as st
from questions import QUESTIONS

st.set_page_config(
    page_title="輸血検査 クイズアプリ",
    page_icon="🩸",
    layout="centered",
)

_PALETTE = [
    "#e74c3c", "#8e44ad", "#2980b9", "#27ae60",
    "#f39c12", "#16a085", "#d35400", "#2c3e50",
    "#c0392b", "#1abc9c",
]
_ICONS = ["🔴", "🟣", "🔵", "🟢", "🟡", "🟤", "⭕", "🔶", "🔷", "🟠"]

def _all_cats():
    return sorted(set(q["category"] for q in QUESTIONS))

def cat_color(cat):
    cats = _all_cats()
    return _PALETTE[cats.index(cat) % len(_PALETTE)] if cat in cats else "#888"

def cat_icon(cat):
    cats = _all_cats()
    return _ICONS[cats.index(cat) % len(_ICONS)] if cat in cats else "⚪"


def init_state():
    defaults = {
        "questions": [], "index": 0, "score": 0,
        "answered": False, "selected": None,
        "mode": "menu", "category": "すべて", "results": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def start_quiz(category: str):
    pool = QUESTIONS if category == "すべて" else [q for q in QUESTIONS if q["category"] == category]
    st.session_state.questions = random.sample(pool, len(pool))
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.selected = None
    st.session_state.mode = "quiz"
    st.session_state.category = category
    st.session_state.results = []


def reset():
    st.session_state.mode = "menu"
    st.session_state.answered = False
    st.session_state.selected = None


def render_menu():
    st.title("🩸 輸血検査 クイズアプリ")
    st.markdown("輸血に関する各分野の問題をランダムに出題します。分野を選んで挑戦しましょう！")
    st.divider()

    total = len(QUESTIONS)
    if st.button(f"⚪ すべて（{total}問）", use_container_width=True, key="btn_all"):
        start_quiz("すべて")
        st.rerun()

    cats = _all_cats()
    cols = st.columns(2)
    for i, cat in enumerate(cats):
        with cols[i % 2]:
            count = sum(1 for q in QUESTIONS if q["category"] == cat)
            icon = cat_icon(cat)
            if st.button(f"{icon} {cat}（{count}問）", use_container_width=True, key=f"btn_{cat}"):
                start_quiz(cat)
                st.rerun()

    st.divider()
    st.caption(f"問題数: 合計 {total} 問　／　分野数: {len(cats)} 分野")


def render_quiz():
    questions = st.session_state.questions
    idx = st.session_state.index

    if idx >= len(questions):
        render_result()
        return

    q = questions[idx]
    total = len(questions)
    is_multi = q.get("multi_answers") is not None

    col1, col2 = st.columns([3, 1])
    with col1:
        color = cat_color(q["category"])
        st.markdown(
            f'<span style="background:{color};color:white;padding:2px 10px;'
            f'border-radius:12px;font-size:0.8em">{q["category"]}</span>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(f"**{idx + 1} / {total}**")

    st.progress(idx / total)
    st.markdown(f"### Q{idx + 1}. {q['question']}")

    if is_multi:
        st.info("※ この問題は複数選択です（2つ選んでください）")

    st.divider()

    answered = st.session_state.answered
    selected = st.session_state.selected

    if not is_multi:
        for ci, choice in enumerate(q["choices"]):
            if answered:
                correct_idx = q["answer"]
                icon = "✅ " if ci == correct_idx else ("❌ " if ci == selected else "　")
                label = f"{icon}{choice}"
            else:
                label = choice
            if st.button(label, key=f"choice_{ci}", disabled=answered, use_container_width=True):
                st.session_state.selected = ci
                st.session_state.answered = True
                correct = (ci == q["answer"])
                if correct:
                    st.session_state.score += 1
                st.session_state.results.append({"correct": correct, "q": q})
                st.rerun()
    else:
        correct_set = set(q["multi_answers"])
        if not answered:
            sel = []
            for ci, choice in enumerate(q["choices"]):
                if st.checkbox(choice, key=f"chk_{ci}"):
                    sel.append(ci)
            if len(sel) > 2:
                st.warning("2つだけ選んでください")
            if st.button("回答する", disabled=(len(sel) != 2)):
                st.session_state.selected = sel
                st.session_state.answered = True
                correct = (set(sel) == correct_set)
                if correct:
                    st.session_state.score += 1
                st.session_state.results.append({"correct": correct, "q": q})
                st.rerun()
        else:
            sel_set = set(selected) if selected else set()
            for ci, choice in enumerate(q["choices"]):
                is_correct = ci in correct_set
                is_chosen = ci in sel_set
                if is_correct and is_chosen:
                    icon = "✅ "
                elif is_correct:
                    icon = "🔷 "
                elif is_chosen:
                    icon = "❌ "
                else:
                    icon = "　"
                st.button(f"{icon}{choice}", key=f"choice_{ci}", disabled=True, use_container_width=True)

    if answered:
        was_correct = st.session_state.results[-1]["correct"] if st.session_state.results else False
        if was_correct:
            st.success("正解！")
        else:
            st.error("不正解")

        with st.expander("解説を見る", expanded=True):
            st.markdown(q["explanation"])

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("次の問題へ →", use_container_width=True, type="primary"):
                st.session_state.index += 1
                st.session_state.answered = False
                st.session_state.selected = None
                st.rerun()
        with col_b:
            if st.button("メニューへ戻る", use_container_width=True):
                reset()
                st.rerun()

    st.divider()
    answered_count = idx + (1 if answered else 0)
    st.caption(f"現在のスコア: {st.session_state.score} / {answered_count} 問正解")


def render_result():
    score = st.session_state.score
    total = len(st.session_state.questions)
    pct = int(score / total * 100)

    st.title("🎉 結果発表")
    st.markdown(f"## {score} / {total} 問正解（{pct}%）")

    if pct >= 90:
        st.success("素晴らしい！輸血のエキスパートです！")
    elif pct >= 70:
        st.info("よくできました！もう少しで完璧です。")
    elif pct >= 50:
        st.warning("半分以上正解！苦手分野を復習しましょう。")
    else:
        st.error("もう一度テキストを見直してみましょう。")

    st.divider()
    st.markdown("### 問題の振り返り")
    for i, r in enumerate(st.session_state.results):
        q = r["q"]
        icon = "✅" if r["correct"] else "❌"
        with st.expander(f"{icon} Q{i+1}. {q['question'][:40]}…"):
            st.markdown(f"**問題:** {q['question']}")
            correct_idxs = q.get("multi_answers") or [q["answer"]]
            correct_text = "　/　".join(q["choices"][i] for i in correct_idxs)
            st.markdown(f"**正解:** {correct_text}")
            st.markdown(f"**解説:** {q['explanation']}")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("同じ分野でもう一度", use_container_width=True, type="primary"):
            start_quiz(st.session_state.category)
            st.rerun()
    with col2:
        if st.button("メニューへ戻る", use_container_width=True):
            reset()
            st.rerun()


init_state()

if st.session_state.mode == "menu":
    render_menu()
elif st.session_state.mode == "quiz":
    render_quiz()
