import traceback

from datetime import datetime


def log_error(error):

    with open(
        "error.log",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(

            f"\n\n[{datetime.now()}]\n"

        )

        f.write(

            traceback.format_exc()
        )