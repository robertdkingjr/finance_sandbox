"""
Stand-alone functions to visualize output of gobble-tick algorithm
"""
import os
from plotly import subplots
from plotly import graph_objects as go
import plotly.express as px

# Unify output location
PLOT_OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'plot'))


def get_plot_output_path(name):
    """Form final plot output path and create intermediate dirs if needed"""
    path = os.path.join(PLOT_OUTPUT_PATH, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def plot_gobble_tick(df, name='gobble_tick.html'):
    """

    Args:
        df (pd.DataFrame): gobble tick output df
        name (str): name of HTML plot with .html extension

    Returns:
        str: path to output HTML file

    """

    # Shape data for plotly express
    melt_df = df.melt(
        id_vars=['tick', 'price', 'Date'],
        value_vars=['bank', 'stock_val', 'value'],
        var_name='money_location',
        value_name='money_value'
    )

    # Create line plot
    fig = px.line(
        melt_df,
        x='Date',
        y='money_value',
        color='money_location',
        hover_data=['tick']
    )

    # Output to HTML file
    path = get_plot_output_path(name=name)
    fig.write_html(path, auto_open=True)
    return path


def multiplot_gobble_tick(df, name='multiplot_gobble_tick.html'):
    """Plot GT algorithm + price data with ROI comparison

    Args:
        df (pd.DataFrame): gobble tick output df
        name (str): name of HTML plot with .html extension

    Returns:
        str: path to output HTML file

    """

    fig = subplots.make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        subplot_titles=['Value distribution', 'Price and performance'],
        specs=[[{"secondary_y": False}], [{"secondary_y": True}]]
    )

    # Add algo data
    fig.add_scatter(row=1, col=1, x=df['Date'], y=df['bank'], name="Cash in Bank")
    fig.add_scatter(row=1, col=1, x=df['Date'], y=df['stock_val'], name="Cash in Stock")
    fig.add_scatter(row=1, col=1, x=df['Date'], y=df['value'], name="Total Value")

    fig.add_scatter(row=2, col=1, x=df['Date'], y=df['price'], name="Price")
    fig.add_scatter(row=2, col=1, x=df['Date'], y=df['gain'], name="ROI", secondary_y=True)
    fig.add_scatter(row=2, col=1, x=df['Date'], y=df['stock_gain'], name="Stock ROI", secondary_y=True)

    # Output to HTML file
    path = get_plot_output_path(name=name)
    fig.write_html(path, auto_open=True)
    return path


if __name__ == '__main__':
    from gobble_tick.algorithm import run_example
    gobble_tick_df = run_example()
    output_path = multiplot_gobble_tick(df=gobble_tick_df, name='gobble_tick_example.html')
    print(f"Output to {output_path}")
