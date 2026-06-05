from datetime import datetime
import pandas as pd


def working_days_between(
    start_date,
    end_date
):

    if not start_date or not end_date:

        return None

    start = pd.to_datetime(
        start_date
    )

    end = pd.to_datetime(
        end_date
    )

    return len(
        pd.bdate_range(
            start,
            end
        )
    ) - 1