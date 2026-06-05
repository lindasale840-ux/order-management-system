from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    JsCode
)


def render_aggrid(
    dataframe,
    height=500,
    pagination=True,
    page_size=5,
    key=None,
    color_sla=False
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

    if (

        color_sla

        and

        "sla_status" in dataframe.columns

    ):

        sla_style = JsCode(
            """

            function(params) {

                if (
                    params.value == "OK"
                ) {

                    return {

                        'backgroundColor': '#d4edda',
                        'color': '#155724',
                        'fontWeight': 'bold'

                    };

                }

                if (
                    params.value == "WARNING"
                ) {

                    return {

                        'backgroundColor': '#fff3cd',
                        'color': '#856404',
                        'fontWeight': 'bold'

                    };

                }

                if (
                    params.value == "OVER SLA"
                ) {

                    return {

                        'backgroundColor': '#f8d7da',
                        'color': '#721c24',
                        'fontWeight': 'bold'

                    };

                }

                return null;

            }

            """
        )

        grid_options["columnDefs"] = [

            {

                "field": col

            }

            for col in dataframe.columns

        ]

        for col in grid_options["columnDefs"]:

            if col["field"] == "sla_status":

                col["cellStyle"] = sla_style

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

        allow_unsafe_jscode=color_sla
    )