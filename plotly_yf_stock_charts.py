import pandas as pd
import plotly.express as px
import plotly.colors
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import datetime

# key = event
# value = (MM, DD, YYYY)
COMPLETION_DATE_LABEL = "Completion (SLAB -> SWKS)"
KEY_DATES = {
    "Announcement": (2021, 4, 22),
    COMPLETION_DATE_LABEL: (2021, 7, 26),
    'ESPP1': (2022, 1, 31),
    "First vesting": (2022, 7, 26),
    'ESPP2': (2023, 1, 31),
    'ESPP3': (2023, 7, 31),
    'ESPP4': (2024, 1, 31),
}
COMPLETION_YYYY, COMPLETION_MM, COMPLETION_DD = KEY_DATES[COMPLETION_DATE_LABEL]
COMPLETION_DATE_STR = f"{COMPLETION_YYYY:04}-{COMPLETION_MM:02}-{COMPLETION_DD:02}"
COMPLETION_DATETIME = datetime.datetime(COMPLETION_YYYY, COMPLETION_MM, COMPLETION_DD).timestamp() * 1000
print(f'COMPLETION_DATE_STR: {COMPLETION_DATE_STR}')

DEFAULT_START = '2021-01-01'

DOLLAR_BILL_COLOR = '#85bb65'


def add_events_to_fig(fig):
    """Annotate figure w/ key events"""

    for i, (event, date) in enumerate(KEY_DATES.items()):
        y, m, d = date
        fig.add_vline(
            x=datetime.datetime(y, m, d).timestamp() * 1000,
            annotation_text=event,

            # space out verically to avoid overlap
            annotation_yref='paper',
            annotation_y=0.99 if i % 2 else 0.04,
        )
    return fig


def get_swks_slab_df(start=DEFAULT_START, to_csv=False):
    """Get ticker data from Yahoo finance"""

    df1 = yf.Ticker('SWKS').history(start=start)
    df1['Ticker'] = 'SWKS'
    df2 = yf.Ticker('SLAB').history(start=start)
    df2['Ticker'] = 'SLAB'
    df = pd.concat([df1, df2], ignore_index=False)
    df['Date'] = df.index

    if to_csv:
        # output to CSV for debugging
        df.to_csv(f'./swks_slab_{start}.csv')

    return df


def get_swks_slab_tdf(start=DEFAULT_START, to_csv=False):
    """Get ticker data from Yahoo finance: tdf = time df - in chronological order by month"""
    swks_df = yf.Ticker('SWKS').history(start=start)
    swks_df['Ticker'] = 'SWKS'
    slab_df = yf.Ticker('SLAB').history(start=start)
    slab_df['Ticker'] = 'SLAB'

    tdf = pd.merge(left=swks_df, right=slab_df, on='Date', suffixes=('_SWKS', '_SLAB'))
    tdf['Date'] = tdf.index

    if to_csv:
        # output to CSV for debugging
        tdf.to_csv(f'./swks_slab_{start}_tdf.csv')

    return tdf


def plot_swks_slab_acquisition():

    df = get_swks_slab_df()

    y_label = 'Stock price ($)'
    melt_df = df.melt(
        id_vars=['Date', 'Ticker'],
        value_vars=['Open', 'Close', 'High', 'Low'],
        value_name=y_label
    )

    # Plot
    fig = px.line(data_frame=melt_df, x='Date', y=y_label, color='Ticker', symbol='variable')
    fig.update_layout(title='Skyworks (SWKS) acquisition of Silicon Labs (SLAB) I&A division')
    add_events_to_fig(fig=fig)

    fig.show()


def plot_color_months(ticker, start, end=None):

    df = yf.Ticker(ticker).history(start=start, end=end)
    df['Ticker'] = ticker
    df['Date'] = df.index
    df['Month'] = df['Date'].dt.month.astype('str')

    y_label = 'Stock price ($)'
    melt_df = df.melt(
        id_vars=['Date', 'Month', 'Ticker'],
        value_vars=['Open', 'Close', 'High', 'Low'],
        value_name=y_label
    )

    # Plot
    fig = px.scatter(
        data_frame=melt_df,
        x='Date',
        y=y_label,
        color='Month',
        color_discrete_sequence=px.colors.qualitative.Dark24,
        symbol='variable',
        title=f'{ticker} (colored by Month)',
    )

    # # add vertical lines showing events
    # add_events_to_fig(fig=fig)

    fig.show()


def get_swks_slab_transfer_bank_df(start_shares, to_csv=False):

    tdf = get_swks_slab_tdf(to_csv=to_csv)

    bank_shares = start_shares
    bank_ticker = 'SLAB'
    data = []
    for row in tdf.to_dict(orient='records'):

        if COMPLETION_DATE_STR in str(row['Date']):
            print(f"ACQUISITION COMPLETION DATE: {row['Date']}")
            new_bank_ticker = 'SWKS'

            price = row[f'Close_{bank_ticker}']
            new_price = row[f'Close_{new_bank_ticker}']
            new_bank_shares = round(bank_shares * price / new_price)

            print(
                f'CONVERTING {bank_shares} * {bank_ticker} @ {price:.2f} -> '
                f'{new_bank_shares} * {new_bank_ticker} @ {new_price:.2f}'
            )

            bank_shares = new_bank_shares
            bank_ticker = new_bank_ticker

        row['Bank Ticker'] = bank_ticker
        row['Bank Shares'] = bank_shares
        row['$'] = bank_shares * row[f'Close_{bank_ticker}']
        data.append(row)

    df = pd.DataFrame(data)

    # Point out transfer of shares
    transition_df = df[df['Date'].astype('str').str.contains(COMPLETION_DATE_STR)]
    transition_index = transition_df.index[0]
    # print(transition_df)

    df['%'] = 100 * df['$'] / df['$'].iloc[transition_index]

    if to_csv:
        df.to_csv('swks_slab_bank.csv')

    return df


def px_plot_swks_slab_share_transfer(start_shares=1000, to_csv=False):
    """Using plotly express (px) attempt to combine:
     - bank value (in $) assuming starting with `start_shares` of SLAB
     - SLAB stock price
     - SWKS stock price

    Args:
        start_shares (int): number of shares of SLAB to own to start bank value
        to_csv (bool): if True, output df to csv for debugging

    Returns:

    """

    df = get_swks_slab_transfer_bank_df(start_shares=start_shares, to_csv=to_csv)

    figures = []
    bank_fig = px.area(
        data_frame=df,
        x='Date',
        y='$',
        color='Bank Ticker',
        color_discrete_map=dict(SLAB='red', SWKS='blue'),
        title='SLAB conversion to SWKS stock',
    )
    figures.append(bank_fig)

    swks_fig = px.line(
        data_frame=df,
        x='Date',
        y='Close_SWKS',
        color='Ticker_SWKS',
        color_discrete_map=dict(SLAB='red', SWKS='blue'),
    )
    swks_fig.update_traces(yaxis="y2")
    figures.append(swks_fig)

    slab_fig = px.line(
        data_frame=df,
        x='Date',
        y='Close_SLAB',
        color='Ticker_SLAB',
        color_discrete_map=dict(SLAB='red', SWKS='blue'),
    )
    slab_fig.update_traces(yaxis="y2")
    figures.append(slab_fig)

    # combine into single figure
    fig = go.Figure(data=sum((fig.data for fig in figures), ()))
    fig.update_layout(
        yaxis2=dict(title="Stock Price ($)", overlaying="y", side="right", tickmode="sync")
    )
    fig.show()


def go_plot_swks_slab_share_transfer(start_shares=1000, to_csv=False, to_html=False, to_png=False):
    """Using plotly graph_objects (go) attempt to combine:
     - bank value (in $) assuming starting with `start_shares` of SLAB
     - SLAB stock price
     - SWKS stock price

    todo:
     - Add SMH/SOX or similar semiconductor ETF for reference (reflect bad years for market)

    Args:
        start_shares (int): number of shares of SLAB to own to start bank value
        to_csv (bool): if True, output df to csv for debugging
        to_html (bool): if True, output plot to html file

    Returns:

    """

    df = get_swks_slab_transfer_bank_df(start_shares=start_shares, to_csv=to_csv)
    solid_color_map = {'SLAB': 'red', 'SWKS': 'blue'}
    transparent_color_map = {'SLAB': 'rgba(255, 0, 0, .1)', 'SWKS': 'rgba(0, 0, 255, .1)'}
    df['Bank Color'] = df['Bank Ticker'].map(solid_color_map)

    # bank_var = '$'
    bank_var = '%'

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for bank_ticker, ticker_df in df.groupby('Bank Ticker'):
        fig.add_trace(go.Scatter(
            x=ticker_df['Date'],
            y=ticker_df[bank_var],
            mode='lines',
            name=bank_var,
            # marker_color=ticker_df['Bank Color'],
            marker_color=DOLLAR_BILL_COLOR,
            line=dict(color=DOLLAR_BILL_COLOR),

            # legendgroup="Bank",
            fill='tozeroy',
            fillcolor=transparent_color_map[bank_ticker]
        ), secondary_y=True)

        for ticker in ['SLAB', 'SWKS']:
            if bank_ticker == ticker:
                color = solid_color_map[ticker]
                # color = 'black'
            else:
                color = transparent_color_map[ticker]
                # color = 'grey'

            fig.add_trace(go.Scatter(
                x=ticker_df['Date'],
                y=ticker_df[f'Close_{ticker}'],
                mode='lines',
                name=ticker,
                marker=dict(color=color),
                # legendgroup="stock price",
            ), secondary_y=False)

    fig.update_layout(
        title='SLAB conversion to SWKS stock',
        yaxis=dict(
            title=dict(text="<b>Stock Price ($)</b>"),
            side="left",
        ),
        yaxis2=dict(
            title=dict(text=f'<b>% value after transition</b>', font=dict(size=14)),
            color=DOLLAR_BILL_COLOR,
            side="right",
            overlaying="y",
            tickmode="sync",
        ),
    )

    fig.add_vline(
        x=COMPLETION_DATETIME,
        annotation_text="<b>SLAB</b> converted to <b>SWKS</b>",
        annotation_yref='paper',
        annotation_y=0.04,
    )

    # use shape for line to allow yref='y2'
    fig.add_shape(
        type="line",
        xref="paper",
        yref="y2",
        x0=0, y0=100, x1=1, y1=100,
        line=dict(color=DOLLAR_BILL_COLOR, dash="dash"),
        label=dict(text="<b>100% value at transition</b>", font=dict(color=DOLLAR_BILL_COLOR))
    )

    # output to file or show locally in browser
    today = datetime.datetime.now().strftime("%Y%m%d")
    path_no_ext = f'./plots/swks_slab_share_transfer_{today}'
    if to_html:
        fig.write_html(f'{path_no_ext}.html')
    else:
        fig.show()

    if to_png:
        fig.write_image(f'{path_no_ext}.png', width=1600, height=700)

    return fig


if __name__ == '__main__':
    # plot_swks_slab_acquisition()
    # plot_color_months(ticker='SWKS', start='2021-01-01')
    # px_plot_swks_slab_share_transfer(to_csv=True)
    go_plot_swks_slab_share_transfer(to_html=True, to_png=True)
