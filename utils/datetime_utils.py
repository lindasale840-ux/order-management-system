import pandas as pd


def convert_utc_columns(df):

    datetime_columns = [

        "created_at",
        "updated_at",
        "deleted_at"

    ]

    for col in datetime_columns:

        if col in df.columns:

            df[col] = (

                pd.to_datetime(
                    df[col],
                    errors="coerce"
                )

                + pd.Timedelta(hours=7)

            )

            df[col] = df[col].dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    return df