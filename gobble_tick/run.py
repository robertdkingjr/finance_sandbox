"""
Get data via finnhub API, run gobble tick algorithm, and plot results to HTML
"""
from finnhub.api import FinnhubRequest
from gobble_tick.algorithm import GobbleTick
import gobble_tick.plot


def run_gobble_tick(finnhub_request, gt):
    """Combine API and algorithm calls into single function

    Args:
        finnhub_request (FinnhubRequest):
        gt (GobbleTick):

    Returns:

    """

    df = finnhub_request.get_candle_data(to_file=True)
    finnhub_request.plot_candle_data(df=df)

    gt_df = gt.run_from_finnhub_df(df=df, to_file=True, input_label=finnhub_request.get_candle_id())
    gobble_tick.plot.multiplot_gobble_tick(df=gt_df, name=f'{finnhub_request.get_candle_id()}\\{gt.get_id()}.html')


if __name__ == '__main__':
    # Try algorithm weekly over last 52 weeks with SLAB
    run_gobble_tick(
        finnhub_request=FinnhubRequest(symbol="SLAB", resolution="W", count=52, from_time=None, to_time=None),
        gt=GobbleTick(bank=50000, gobble_amount=1000, exit_rate=0.03)
    )

    # Try algorithm daily over last 100 days with SLAB
    run_gobble_tick(
        finnhub_request=FinnhubRequest(symbol="SLAB", resolution="D", count=100, from_time=None, to_time=None),
        gt=GobbleTick(bank=50000, gobble_amount=1000, exit_rate=0.03)
    )
