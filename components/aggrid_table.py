from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode
)


def render_aggrid(
    dataframe,
    height=500,
    pagination=True,
    page_size=5,
    key=None
):

    gb = GridOptionsBuilder.from_dataframe(
        dataframe
    )

    # =========================
    # DEFAULT COLUMN
    # =========================

    gb.configure_default_column(

        sortable=True,

        filter=True,

        resizable=True,

        floatingFilter=True,

        editable=False
    )

    # =========================
    # PAGINATION
    # =========================

    if pagination:

        gb.configure_pagination(

            enabled=True,

            paginationAutoPageSize=False,

            paginationPageSize=page_size
        )

    # =========================
    # SELECTION
    # =========================

    gb.configure_selection(
        selection_mode="multiple",
        use_checkbox=False
    )

    grid_options = gb.build()

    # Cho phép copy
    grid_options["enableRangeSelection"] = True
    grid_options["enableCellTextSelection"] = True
    grid_options["ensureDomOrder"] = True

    return AgGrid(

        dataframe,

        gridOptions=grid_options,

        height=height,

        width="100%",
        
        key=key,

        update_mode=GridUpdateMode.NO_UPDATE,

        fit_columns_on_grid_load=True,

        enable_enterprise_modules=False,

        allow_unsafe_jscode=False
    )