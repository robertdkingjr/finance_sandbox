"""
Gobble Tick Algorithm

todo: use resistance/support indicators to dynamically change the gobble amount
todo: use resistance/support indicators to dynamically change the exit rate

"""
import os
import pandas as pd
from pandas import DataFrame
pd.options.display.width = 0
pd.options.display.max_rows = 1000
pd.options.display.max_columns = 999
pd.options.display.max_colwidth = 999


class GobbleTick:
    """Defines the most basic version of the algorithm
    - Buy ("gobble") a set amount (in $) of stock at regular intervals ("ticks")
    - Set the target exit threshold for each purchase at the purchase price * (1 + exit_rate)
    - For example: if exit_rate = 0.03, all purchases will be sold as soon as the stock has risen 3%
    """

    DATA_OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))

    def __init__(self, bank, gobble_amount, exit_rate):
        """

        Args:
            bank (int): amount of money in bank (in dollars)
            gobble_amount (int): amount of money to use to purchase stock each tick
            exit_rate (float): rate above buying price to target to sell (e.g. 0.01 = sell at 1% above buying price)
        """
        # Make sure output paths exist
        os.makedirs(self.DATA_OUTPUT_PATH, exist_ok=True)

        self.bank = bank
        self.gobble_amount = gobble_amount
        self.exit_rate = exit_rate

    def get_id(self):
        """Create unique ID to store results"""
        return f"{self.bank}_{self.gobble_amount}_{self.exit_rate}"

    def run_from_finnhub_df(self, df, to_file=True, input_label=None):
        """Run algorithm on data directly from Finnhub by selecting the 'o' (open) column as the price target"""
        if input_label is not None:
            self.DATA_OUTPUT_PATH = os.path.join(self.DATA_OUTPUT_PATH, input_label)
            os.makedirs(self.DATA_OUTPUT_PATH, exist_ok=True)

        df['price'] = df['o']
        return self.run(price_df=df, to_file=to_file)

    def run(self, price_df, to_file=True, input_label=None):
        """Run and store the algorithm in tabular form for tweaking and performance review

        Args:
            price_df (DataFrame): pandas DataFrame containing 'price' column
            to_file (bool): if True, output data to CSV file
            input_label (str): optional additional dir level to label based off of input dataset

        Returns:
            DataFrame: df containing full algorithm context

        """
        if input_label is not None:
            self.DATA_OUTPUT_PATH = os.path.join(self.DATA_OUTPUT_PATH, input_label)
            os.makedirs(self.DATA_OUTPUT_PATH, exist_ok=True)

        price_df_columns = price_df.columns
        if 'price' in price_df_columns:
            df = price_df
        else:
            raise ValueError(f"price_df does not contain 'price' column: {price_df_columns}")

        bank = self.bank
        gobble_amount = self.gobble_amount
        exit_rate = self.exit_rate

        df['enter'] = [None] * len(df.index)  # cash spent on opening position
        df['target'] = [None] * len(df.index)  # target selling price
        df['exit'] = [None] * len(df.index)  # cash made on exiting position

        df['profit'] = [None] * len(df.index)  # profit made on exiting all positions on this tick

        df['bank'] = [None] * len(df.index)  # value held in cash
        df['stock'] = [None] * len(df.index)  # num stocks held
        df['stock_val'] = [None] * len(df.index)  # value held in stocks
        df['value'] = [None] * len(df.index)  # value held total

        # df['price'] = df['c']  # use closing stock price in this example
        df['tick'] = df.index  # tick = arbitrary unit of time, in this case use index of passed in data set
        df['gobble'] = [None] * len(df.index)  # gobble = num stocks to purchase at given tick

        # Iterate over rows (downwards) to simulate passing time
        for i, row in df.iterrows():
            price = row['price']

            # Seed the bank for the first row
            bank_start = bank if i == 0 else df.at[i-1, 'bank']

            # Limited to money in the bank
            if bank_start < gobble_amount:
                buy_in = bank_start
            else:
                buy_in = gobble_amount

            # Calculate tick buy-in
            gobble = round(buy_in / price)
            enter_total = gobble * price
            target = price * (1 + exit_rate)

            df.at[i, 'gobble'] = gobble
            df.at[i, 'enter'] = enter_total
            df.at[i, 'target'] = target

            past_df = df[df.index <= i]
            # print(past_df)

            # All positions which are currently open (held as stock)
            open_df = past_df[pd.isnull(past_df['exit'])]

            # All positions which have reached the target and can be sold
            close_df = open_df[(open_df['target'] <= price)]

            # Exercise close and sum all gains
            closed_returns = 0
            closed_profit = 0
            for close_i, close_row in close_df.iterrows():
                # EXIT HERE
                exit_total = price * close_row['gobble']
                df.at[close_i, 'exit'] = exit_total
                closed_returns += exit_total

                exit_profit = exit_total - close_row['enter']
                closed_profit += exit_profit

            # Amount of money made exiting positions this tick
            df.at[i, 'profit'] = closed_profit

            # Calculate bank value after this action
            bank_value = bank_start - enter_total
            bank_value += closed_returns
            df.at[i, 'bank'] = bank_value

            # Calculate stock value after this action
            still_open_df = df[(df.index <= i) & pd.isnull(df['exit'])]
            num_stocks_open = still_open_df['gobble'].sum()
            df.at[i, 'stock'] = num_stocks_open
            stock_value = price * num_stocks_open
            df.at[i, 'stock_val'] = stock_value

            # Calculate total value after this action
            total_value = bank_value + stock_value
            df.at[i, 'value'] = total_value

            # print(df.head(10))
            # if i > 10:
            #     break

        df['gain'] = df['value'] / bank
        df['stock_gain'] = df['price'] / df.at[0, 'price']

        if to_file:
            self.output_data_to_file(df=df)

        return df

    def output_data_to_file(self, df):
        """Output algorithm data to file

        Args:
            df (DataFrame): output of GobbleTick.run method

        Returns:
            str: output path

        """
        output_path = os.path.join(self.DATA_OUTPUT_PATH, f"{self.get_id()}.csv")
        df.to_csv(output_path)
        return output_path


def run_example():
    import finnhub.api

    # Get example stock data and use 'o' (open) data for price input to algorithm
    example_df = finnhub.api.run_example(plot=False)
    example_df['price'] = example_df['o']

    # Run algorithm and show as table
    gt = GobbleTick(bank=50000, gobble_amount=1000, exit_rate=0.04)
    df = gt.run(price_df=example_df, to_file=True, input_label="example")

    return df


if __name__ == '__main__':

    gobble_tick_df = run_example()
    print(gobble_tick_df.head(5))
