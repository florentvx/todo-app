import streamlit as st
from datetime import date
import todo_manager as tm
from todo_cls import Todo

st.set_page_config(page_title="Todo List", page_icon="✅", layout="centered")
st.title("✅ Todo List")

priority_icon = {"high": "🔴", "normal": "🟡", "low": "🟢"}


@st.dialog("Todo details", width="large")
def show_todo_detail(todo_id: str):
    """The 'window in window' - full notes + editable Done status live here."""
    todos_by_id : dict[str, Todo] = {t.id: t for t in tm.list_todos()}
    t = todos_by_id.get(todo_id)

    if not t:
        st.warning("This todo no longer exists (probably deleted).")
        if st.button("Close"):
            st.session_state.open_todo_id = None
            st.rerun()
        return

    st.subheader(t.text)
    st.caption(f"Created {t.created_at} · priority: {t.priority}")

    done = st.checkbox("Done", value=t.done)
    notes = st.text_area("Notes", value=t.comment, height=220, placeholder="No notes yet.")

    delivery = None
    
    current_delivery = date.fromisoformat(t.get_delivery_date())
    delivery = st.date_input("Delivery date", value=current_delivery, min_value="2000-01-01")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", use_container_width=True, type="primary"):
            tm.set_done(todo_id, done)
            tm.update_comment(todo_id, notes)
            tm.update_delivery_date(todo_id, delivery.isoformat())
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
    delivery = st.date_input("Delivery date", value=date.today())
    submitted = st.form_submit_button("Add", use_container_width=True)
    if submitted and new_text.strip():
        tm.add_todo(new_text, priority, new_comment, delivery_date=delivery.isoformat())
        st.rerun()

st.divider()

# --- Controls ---
col_filter, col_sort, col_limit = st.columns([1, 1, 1])

with col_filter:
    filter_choice = st.radio("Show", ["All", "Active", "Done"], horizontal=True, label_visibility="collapsed")

with col_sort:
    sort_field = st.selectbox("Sort by", ["Delivery date", "Created date", "Priority"], index=0, label_visibility="collapsed")

with col_limit:
    limit_choice = st.selectbox("Show", ["10", "25", "50", "All"], index=1, label_visibility="collapsed")

# --- Fetch & filter ---
todos = tm.list_todos()

if filter_choice == "Active":
    todos = [t for t in todos if not t.done]
elif filter_choice == "Done":
    todos = [t for t in todos if t.done]

# --- Sort ---
priority_order = {"high": 0, "normal": 1, "low": 2}

if sort_field == "Delivery date":
    todos = sorted(todos, key=lambda t: t.get_delivery_date())
elif sort_field == "Created date":
    todos = sorted(todos, key=lambda t: t.created_at, reverse=True)
elif sort_field == "Priority":
    todos = sorted(todos, key=lambda t: priority_order.get(t.priority, 1))

# --- Limit ---
if limit_choice != "All":
    todos = todos[:int(limit_choice)]

if not todos:
    st.info("Nothing here yet.")

# --- List ---
for t in todos:
    c1, c2 = st.columns([5, 1])
    with c1:
        status_icon = "✅" if t.done else "◻️"
        p_icon = priority_icon.get(t.priority, "🟡")
        delivery = t.get_delivery_date()[:10] if t.delivery_date else ""
        label = f"{p_icon} {status_icon}  {t.text}  \n*{delivery}*"
        if st.button(label, key=f"open_{t.id}", use_container_width=True):
            st.session_state.open_todo_id = t.id
            st.rerun()
    with c2:
        if st.button("🗑️", key=f"del_{t.id}"):
            tm.delete_todo(t.id)
            st.rerun()

# Open the dialog if a todo was clicked (survives the rerun above)
if st.session_state.get("open_todo_id"):
    show_todo_detail(st.session_state.open_todo_id)
