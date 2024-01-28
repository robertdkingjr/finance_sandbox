import pandas as pd
import plotly.express as px
import yfinance as yf
import datetime

# key = event
# value = (MM, DD, YYYY)
KEY_DATES = {
    "Announcement": (2021, 4, 22),
    "Completion (SLAB converted to SWKS)": (2021, 7, 26),
    "First vesting": (2022, 7, 31),
}


def plot_swks_slab_acquisition():

    # get ticker data from Yahoo finance
    start = '2021-01-01'  # show some time before acquisition announcement
    df1 = yf.Ticker('SWKS').history(start=start)
    df2 = yf.Ticker('SLAB').history(start=start)
    df = pd.merge(left=df1, right=df2, left_index=True, right_index=True, suffixes=("_SWKS", "_SLAB"))
    df['Date'] = df.index

    # output to CSV for debugging
    df.to_csv(f'./swks_slab_{start}.csv')

    # Melt combined data for plotting
    vars_suffixes = []
    for ticker in ['SWKS', 'SLAB']:
        for var in ['Open', 'Close', 'High', 'Low']:
            vars_suffixes.append(f'{var}_{ticker}')
    y_label = 'Stock price ($)'
    melt_df = df.melt(id_vars=['Date'], value_vars=vars_suffixes, value_name=y_label)

    # Plot
    fig = px.line(data_frame=melt_df, x='Date', y=y_label, color='variable')
    fig.update_layout(title='Skyworks (SWKS) acquisition of Silicon Labs (SLAB) I&A division')

    # Annotate w/ key events
    for i, (event, date) in enumerate(KEY_DATES.items()):
        y, m, d = date
        fig.add_vline(
            x=datetime.datetime(y, m, d).timestamp() * 1000,
            annotation_text=event,

            # space out verically to avoid overlap
            annotation_yref='paper',
            annotation_y=0.99 if i % 2 else 0.04,
        )

    fig.show()


if __name__ == '__main__':
    plot_swks_slab_acquisition()
