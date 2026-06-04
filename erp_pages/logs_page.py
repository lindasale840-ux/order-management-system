import streamlit as st

from repositories.log_repository import (
    LogRepository
)

from components.aggrid_table import (
    render_aggrid
)

from utils.excel_export import (
    dataframe_to_excel
)


def show_logs_page():

    st.title("Logs")

    # =========================
    # LOG SUMMARY
    # =========================

    total_logs = (
        LogRepository.get_log_count()
    )

    st.metric(
        "Total Logs",
        total_logs
    )

    # =========================
    # DELETE ALL LOGS
    # =========================

    with st.expander(
        "⚠️ Maintenance"
    ):

        st.warning(
            "Delete all logs cannot be undone."
        )

        confirm_delete = st.checkbox(
            "I understand and want to delete all logs"
        )

        if st.button(
            "🗑 Delete All Logs"
        ):

            if not confirm_delete:

                st.error(
                    "Please confirm first"
                )

            else:

                LogRepository.delete_all_logs()

                st.success(
                    "All logs deleted"
                )

                st.rerun()

    st.divider()

    # =========================
    # PAGE SIZE
    # =========================

    page_size = st.selectbox(

        "Rows per page",

        [5, 10, 20, 50],

        index=0,

        key="logs_page_size"
    )

    # =========================
    # LOAD DATA
    # =========================

    df = (
        LogRepository.get_logs()
    )

    action_icon = {

        "SYNC_ORDER": "📊",

        "SAVE_INVOICE": "💰",

        "DELETE_ORDER": "🗑",

        "ADD_TRACKING": "📨",

        "DELETE_TRACKING": "❌"
    }

    df["action"] = df["action"].apply(

        lambda x:
        f"{action_icon.get(x,'📄')} {x}"
    )

    # =========================
    # SEARCH + FILTER
    # =========================

    col1, col2 = st.columns(2)

    with col1:

        search_text = st.text_input(
            "🔍 Search"
        )

    with col2:

        action_list = ["ALL"] + sorted(
            df["action"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_action = st.selectbox(
            "Action",
            action_list
        )

    if search_text:

        mask = (
            df.astype(str)
            .apply(
                lambda col:
                col.str.contains(
                    search_text,
                    case=False,
                    na=False
                )
            )
            .any(axis=1)
        )

        df = df[mask]

    if selected_action != "ALL":

        df = df[
            df["action"]
            == selected_action
        ]

    # =========================
    # GRID
    # =========================

    render_aggrid(

        df,

        height=500,

        page_size=page_size
    )

    # =========================
    # EXPORT
    # =========================

    excel_data = dataframe_to_excel({

        "Logs": df
    })

    st.download_button(

        label="📥 Export Logs Excel",

        data=excel_data,

        file_name="system_logs.xlsx",

        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )