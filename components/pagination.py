import math
import streamlit as st


def paginate_dataframe(
    df,
    page_name,
    default_page_size=5
):

    total_rows = len(df)

    # =========================
    # PAGE SIZE
    # =========================

    page_size_key = (
        f"{page_name}_page_size"
    )

    if page_size_key not in st.session_state:

        st.session_state[
            page_size_key
        ] = default_page_size

    page_size = st.selectbox(

        "Rows per page",

        [5, 10, 20, 50],

        index=[5, 10, 20, 50].index(
            st.session_state[
                page_size_key
            ]
        ),

        key=page_size_key
    )

    # =========================
    # TOTAL PAGE
    # =========================

    total_pages = max(

        math.ceil(
            total_rows / page_size
        ),

        1
    )

    # =========================
    # CURRENT PAGE
    # =========================

    current_page_key = (
        f"{page_name}_current_page"
    )

    if current_page_key not in st.session_state:

        st.session_state[
            current_page_key
        ] = 1

    # Prevent overflow

    if (
        st.session_state[
            current_page_key
        ] > total_pages
    ):

        st.session_state[
            current_page_key
        ] = total_pages

    # =========================
    # PAGE SELECTOR
    # =========================

    selected_page = st.number_input(

        "Page",

        min_value=1,

        max_value=total_pages,

        value=st.session_state[
            current_page_key
        ],

        step=1,

        key=f"{page_name}_page_input"
    )

    st.session_state[
        current_page_key
    ] = selected_page

    current_page = st.session_state[
        current_page_key
    ]

    # =========================
    # DATA SLICE
    # =========================

    start_idx = (
        (current_page - 1)
        * page_size
    )

    end_idx = (
        start_idx
        + page_size
    )

    paginated_df = df.iloc[
        start_idx:end_idx
    ]

    # =========================
    # NAVIGATION BUTTON
    # =========================

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col1:

        if st.button(

            "⬅ Previous",

            key=f"{page_name}_prev"
        ):

            if current_page > 1:

                st.session_state[
                    current_page_key
                ] -= 1

                st.rerun()

    with col2:

        st.markdown(f"""

        <div style='
            text-align:center;
            font-weight:bold;
            padding-top:8px;
            font-size:18px;
        '>

        Page {current_page}
        / {total_pages}

        <br>

        Total Rows:
        {total_rows}

        </div>

        """, unsafe_allow_html=True)

    with col3:

        if st.button(

            "Next ➡",

            key=f"{page_name}_next"
        ):

            if current_page < total_pages:

                st.session_state[
                    current_page_key
                ] += 1

                st.rerun()

    return paginated_df