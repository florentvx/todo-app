import streamlit as st
import todo_manager as tm

st.set_page_config(page_title="Todo List", page_icon="✅", layout="centered")
st.title("✅ Todo List")

priority_icon = {"high": "🔴", "normal": "🟡", "low": "🟢"}


@st.dialog("Todo details", width="large")
def show_todo_detail(todo_id: str):
    """The 'window in window' - full notes + editable Done status live here."""
    todos_by_id = {t["id"]: t for t in tm.list_todos()}
    t = todos_by_id.get(todo_id)

    if not t:
        st.warning("This todo no longer exists (probably deleted).")
        if st.button("Close"):
            st.session_state.open_todo_id = None
            st.rerun()
        return

    st.subheader(t["text"])
    st.caption(f"Created {t['created_at']} · priority: {t['priority']}")

    done = st.checkbox("Done", value=t["done"])
    notes = st.text_area("Notes", value=t.get("comment", ""), height=220, placeholder="No notes yet.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True, type="primary"):
            tm.set_done(todo_id, done)
            tm.update_comment(todo_id, notes)
            st.session_state.open_todo_id = None
            st.rerun()
    with col2:
        if st.button("Close", use_container_width=True):
            st.session_state.open_todo_id = None
            st.rerun()


# --- Add new todo ---
with st.form("add_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_text = st.text_input("New todo", label_visibility="collapsed", placeholder="What needs doing?")
    with col2:
        priority = st.selectbox("Priority", ["normal", "high", "low"], label_visibility="collapsed")
    new_comment = st.text_area(
        "Notes",
        label_visibility="collapsed",
        placeholder="Optional notes / details (as long as you like)...",
        height=100,
    )
    submitted = st.form_submit_button("Add", use_container_width=True)
    if submitted and new_text.strip():
        tm.add_todo(new_text, priority, new_comment)
        st.rerun()

st.divider()

# --- Filter ---
filter_choice = st.radio("Show", ["All", "Active", "Done"], horizontal=True, label_visibility="collapsed")

todos = tm.list_todos()
if filter_choice == "Active":
    todos = [t for t in todos if not t["done"]]
elif filter_choice == "Done":
    todos = [t for t in todos if t["done"]]

if not todos:
    st.info("Nothing here yet.")

# --- List (title + priority + status only - click to see/edit details) ---
for t in todos:
    c1, c2 = st.columns([5, 1])
    with c1:
        status_icon = "✅" if t["done"] else "◻️"
        p_icon = priority_icon.get(t["priority"], "🟡")
        label = f"{p_icon} {status_icon}  {t['text']}"
        if st.button(label, key=f"open_{t['id']}", use_container_width=True):
            st.session_state.open_todo_id = t["id"]
            st.rerun()
    with c2:
        if st.button("🗑️", key=f"del_{t['id']}"):
            tm.delete_todo(t["id"])
            st.rerun()

# Open the dialog if a todo was clicked (survives the rerun above)
if st.session_state.get("open_todo_id"):
    show_todo_detail(st.session_state.open_todo_id)
