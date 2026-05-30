def format_currency(value):

    try:

        return "{:,.0f}".format(
            float(value)
        )

    except:

        return value