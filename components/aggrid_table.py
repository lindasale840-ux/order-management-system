from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode
)


def render_aggrid(
    dataframe,
    height=500,
    pagination=True,
    page_size=5
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

        floatingFilter=True
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
        selection_mode="single"
    )

    grid_options = gb.build()

    # =========================
    # RENDER GRID
    # =========================

    return AgGrid(

        dataframe,

        gridOptions=grid_options,

        height=height,

        width="100%",

        update_mode=GridUpdateMode.NO_UPDATE,

        fit_columns_on_grid_load=True,

        enable_enterprise_modules=False,

        allow_unsafe_jscode=False
    )