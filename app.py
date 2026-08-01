import streamlit as st

from datetime import date
import calendar
import html
import todo_manager as tm
from todo_cls import Todo
import calendar_manager as cm
from calendar_cls import CALENDAR_COLORS

st.set_page_config(page_title="Todo App", page_icon="✅", layout="wide")

priority_icon = {"high": "🔴", "normal": "🟡", "low": "🟢"}


@st.dialog("Todo details", width="large")
def show_todo_detail(todo_id: str):
    todos_by_id: dict[str, Todo] = {t.id: t for t in tm.list_todos()}
    t = todos_by_id.get(todo_id)

    if not t:
        st.warning("This todo no longer exists (probably deleted).")
        if st.button("Close"):
            st.session_state.open_todo_id = None
            st.rerun()
        return

    st.subheader(t.text)
    st.caption(f"Created {t.created_at} \u00b7 priority: {t.priority}")

    done = st.checkbox("Done", value=t.done)
    notes = st.text_area("Notes", value=t.comment, height=220, placeholder="No notes yet.")

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


@st.dialog("Edit day", width="small")
def show_calendar_edit_dialog(date_str: str):
    entry = cm.get_entry(date_str)

    st.subheader(date_str)
    title = st.text_input("Title", value=entry.title if entry else "", placeholder="Enter title...")
    notes = st.text_area("Notes", value=entry.notes if entry else "", placeholder="Enter notes...", height=150)

    color_names = list(CALENDAR_COLORS.keys())
    current_color = entry.color if entry and entry.color in color_names else "default"
    color_idx = color_names.index(current_color)
    color = st.selectbox("Color", color_names, index=color_idx,
                         format_func=lambda c: c.capitalize())

    st.markdown(
        f"<div style='background:{CALENDAR_COLORS[color]};height:40px;border-radius:6px;margin-bottom:12px;'></div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save", type="primary", use_container_width=True):
            cm.save_entry(date_str, title.strip(), notes.strip(), color)
            st.session_state.edit_date = None
            st.rerun()
    with c2:
        if entry:
            if st.button("Delete", use_container_width=True):
                cm.delete_entry(date_str)
                st.session_state.edit_date = None
                st.rerun()


def todo_page():
    st.title("Todo List")

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

    col_filter, col_sort, col_limit = st.columns([1, 1, 1])

    with col_filter:
        filter_choice = st.radio("Show", ["All", "Active", "Done"], horizontal=True, label_visibility="collapsed")

    with col_sort:
        sort_field = st.selectbox("Sort by", ["Delivery date", "Created date", "Priority"], index=0, label_visibility="collapsed")

    with col_limit:
        limit_choice = st.selectbox("Show", ["10", "25", "50", "All"], index=1, label_visibility="collapsed")

    todos = tm.list_todos()

    if filter_choice == "Active":
        todos = [t for t in todos if not t.done]
    elif filter_choice == "Done":
        todos = [t for t in todos if t.done]

    priority_order = {"high": 0, "normal": 1, "low": 2}

    if sort_field == "Delivery date":
        todos = sorted(todos, key=lambda t: t.get_delivery_date())
    elif sort_field == "Created date":
        todos = sorted(todos, key=lambda t: t.created_at, reverse=True)
    elif sort_field == "Priority":
        todos = sorted(todos, key=lambda t: priority_order.get(t.priority, 1))

    if limit_choice != "All":
        todos = todos[: int(limit_choice)]

    if not todos:
        st.info("Nothing here yet.")

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
            if st.button("Delete", key=f"del_{t.id}"):
                tm.delete_todo(t.id)
                st.rerun()

    if st.session_state.get("open_todo_id"):
        show_todo_detail(st.session_state.open_todo_id)


def calendar_page():
    st.title("Calendar")
    st.caption("Click on any day to add or edit an entry.")

    if "cal_year" not in st.session_state:
        today = date.today()
        st.session_state.cal_year = today.year
        st.session_state.cal_month = today.month

    year = st.session_state.cal_year
    month = st.session_state.cal_month

    c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
    with c1:
        if st.button("◀", use_container_width=True):
            st.session_state.edit_date = None
            new_month = month - 1
            new_year = year
            if new_month == 0:
                new_month = 12
                new_year -= 1
            st.session_state.cal_month = new_month
            st.session_state.cal_year = new_year
            st.rerun()
    with c2:
        st.header(f"{calendar.month_name[month]} {year}", anchor=False)
    with c3:
        if st.button("▶", use_container_width=True):
            st.session_state.edit_date = None
            new_month = month + 1
            new_year = year
            if new_month == 13:
                new_month = 1
                new_year += 1
            st.session_state.cal_month = new_month
            st.session_state.cal_year = new_year
            st.rerun()
    with c4:
        if st.button("Today", use_container_width=True):
            st.session_state.edit_date = None
            today = date.today()
            st.session_state.cal_year = today.year
            st.session_state.cal_month = today.month
            st.rerun()

    entries = cm.list_entries()
    entry_map = {e.date: e for e in entries}

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    today_str = date.today().isoformat()
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for i, dn in enumerate(day_names):
        if i == 0:
            hcols = st.columns(7)
        hcols[i].markdown(f"<div style='text-align:center;font-weight:bold;padding:8px 4px;'>{dn}</div>", unsafe_allow_html=True)

    for week in month_days:
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            if day_num == 0:
                continue
            date_str = f"{year}-{month:02d}-{day_num:02d}"
            entry = entry_map.get(date_str)

            if entry:
                bg = CALENDAR_COLORS.get(entry.color, "#ffffff")
                tc = "#ffffff" if entry.color not in ("default", "yellow") else "#212529"
            else:
                bg = CALENDAR_COLORS["default"]
                tc = "#212529"

            is_today = date_str == today_str
            border = "2px solid #228be6" if is_today else "1px solid #dee2e6"
            title = entry.title if entry and entry.title else ""
            notes = entry.notes if entry and entry.notes else ""
            tooltip = notes if notes else title
            esc_title = html.escape(title).replace("\n", "<br>")
            esc_tooltip = html.escape(tooltip).replace("\n", "&#10;")
            notes_badge = ""
            cell_position = ""
            if notes and not title:
                cell_position = "position:relative;"
                notes_badge = (
                    '<div style="position:absolute;right:6px;bottom:6px;width:8px;height:8px;'
                    'border-radius:50%;background:#212529;"></div>'
                )

            with cols[i]:
                st.markdown(
                    f'<div style="display:flex;flex-direction:column;{cell_position}color:{tc};background:{bg};'
                    f'border:{border};border-radius:6px;padding:8px;min-height:90px;'
                    f'box-sizing:border-box;" title="{esc_tooltip}">'
                    f'<div style="font-weight:bold;font-size:18px;line-height:1.3;">{day_num}</div>'
                    f'<div style="flex:1;display:flex;align-items:center;justify-content:center;'
                    f'font-size:13px;text-align:center;overflow:hidden;">{esc_title}</div>'
                    f'{notes_badge}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("✎", key=f"cal_{date_str}", use_container_width=True):
                    st.session_state.edit_date = date_str
                    st.rerun()

    if st.session_state.get("edit_date"):
        show_calendar_edit_dialog(st.session_state.edit_date)


todo_pg = st.Page(todo_page, title="Todo List", icon="✅")
cal_pg = st.Page(calendar_page, title="Calendar", icon="📅")
pg = st.navigation([todo_pg, cal_pg])
pg.run()
