"""
https://finnhub.io/docs/api#stock-candles
"""
import os
import sys
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

import logging

# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__file__)


class FinnhubRequest:

    CANDLE_API = "https://finnhub.io/api/v1/stock/candle"
    TOKEN = 'br6t2hnrh5rdamtpc4ng'
    CANDLE_DATA_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'candle_data'))
    CANDLE_PLOT_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'candle_plot'))

    def __init__(self, symbol, resolution, count=None, from_time=None, to_time=None):
        """

        Args:
            symbol: REQUIRED stock symbol
            resolution: REQUIRED Supported resolution includes 1, 5, 15, 30, 60, D, W, M.
              Some timeframes might not be available depending on the exchange.
            count: UNDOCUMENTED Requested number of points at given resolution
            from_time: UNIX timestamp. Interval initial value. If count is not provided, this field is required
            to_time: UNIX timestamp. Interval end value. If count is not provided, this field is required

        """
        if count is None and (from_time is None or to_time is None):
            raise ValueError("Must specify count OR (from_time AND to_time)")

        # Ensure output paths exist
        os.makedirs(self.CANDLE_DATA_OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.CANDLE_PLOT_OUTPUT_DIR, exist_ok=True)

        self.symbol = symbol
        self.resolution = resolution
        self.count = count
        self.from_time = from_time
        self.to_time = to_time

    def get_candle_id(self):
        """Create unique id for candle dataset pulled from finnhub"""

        # e.g. 52W or 365D
        count_id = f"{self.count}{self.resolution}"

        # e.g. 1234_to_5678_by_60
        from_to_id = f"{self.from_time}_to_{self.to_time}_by_{self.resolution}"

        # Select id depending on inputs
        time_range_id = count_id if self.count is not None else from_to_id

        return f"{self.symbol}_{time_range_id}"

    def get_candle_request_url(self):
        """Form API request URL"""

        symbol_arg = f"symbol={self.symbol}"  # Note: symbol arg first - no &
        res_arg = f"&resolution={self.resolution}"
        count_arg = f"&count={self.count}" if self.count is not None else ""
        from_arg = f"&from={self.from_time}" if self.from_time is not None else ""
        to_arg = f"&to={self.to_time}" if self.to_time is not None else ""
        token_arg = f"&token={self.TOKEN}"

        return f"{self.CANDLE_API}?{symbol_arg}{res_arg}{count_arg}{from_arg}{to_arg}{token_arg}"

    def get_candle_data(self, from_file=True, to_file=True):
        """Send API request to finnhub for data and convert JSON into DataFrame

        Args:
            from_file (bool): if True, try pulling data from CSV file before sending API request
            to_file (bool): if True, save data to CSV file so that it can be pulled in the future without an API request

        Returns:

        """
        csv_file_path = self.get_candle_data_file_path()
        data_exists_on_file = os.path.exists(csv_file_path)

        # Get from file if it exists
        if from_file and data_exists_on_file:
            df = pd.read_csv(csv_file_path, index_col=0)

        # Otherwise get data from API request
        else:
            r = requests.get(self.get_candle_request_url())
            logger.info(r)
            json_data = r.json()
            logger.debug(json_data)

            # todo catch json_data being 'no_data'
            df = pd.DataFrame(json_data)
            df['Date'] = df['t'].apply(datetime.fromtimestamp)

        # Write to CSV file if query doesn't already exist
        if to_file and not data_exists_on_file:
            df.to_csv(csv_file_path)

        return df

    def get_candle_data_file_path(self):
        return os.path.join(self.CANDLE_DATA_OUTPUT_DIR, f"{self.get_candle_id()}.csv")

    def quick_candle_line_data(self, df):
        """Plot candle data in simple line plot"""
        melt_df = df.melt(id_vars=['Date'], value_vars=['o', 'c', 'h', 'l'])
        fig = px.line(data_frame=melt_df, x='Date', y='value', color='variable')
        fig.update_layout(title=self.symbol)
        fig.write_html(f'./basic_{self.get_candle_id()}.html')

    def plot_candle_data(self, df, auto_open=True):
        """Convenient method to visualize candle data"""
        fig = go.Figure(data=[go.Candlestick(x=df['Date'], open=df['o'], high=df['h'], low=df['l'], close=df['c'])])
        fig.write_html(os.path.join(self.CANDLE_PLOT_OUTPUT_DIR, f'{self.get_candle_id()}.html'), auto_open=auto_open)


def run_example(plot=True):
    """Example: 52 weeks of SLAB stock"""
    example_request = FinnhubRequest(symbol="SLAB", resolution="W", count=52)
    df = example_request.get_candle_data()
    if plot:
        example_request.plot_candle_data(df=df, auto_open=True)
    return df


if __name__ == '__main__':
    run_example()
