import requests

from bokeh.plotting import figure
from bokeh.palettes import Category20
from bokeh.models.widgets import PreText
from bokeh.models import BooleanFilter, CDSView, BoxAnnotation, Band, Span, Select, LinearAxis, DataRange1d, Range1d
from bokeh.models.formatters import PrintfTickFormatter, NumeralTickFormatter

WIDTH_PLOT = 1500

RED = Category20[7][6]
GREEN = Category20[5][4]

BLUE = Category20[3][0]
BLUE_LIGHT = Category20[3][1]

ORANGE = Category20[3][2]
PURPLE = Category20[9][8]
BROWN = Category20[11][10]

TOOLS = 'pan,wheel_zoom,reset'


# Main chart for stock prices with candlestick and Bolinger bands
def plot_stock_price(stock):
    p = figure(x_axis_type="datetime", plot_width=WIDTH_PLOT, plot_height=400,
               title="Stock price + Bollinger Bands (2 std)",
               tools=TOOLS, toolbar_location='above')

    inc = stock.data['close'] > stock.data['open']
    dec = stock.data['open'] > stock.data['close']
    view_inc = CDSView(source=stock, filters=[BooleanFilter(inc)])
    view_dec = CDSView(source=stock, filters=[BooleanFilter(dec)])

    width = 35000000

    p.segment(x0='date', x1='date', y0='low', y1='high', color=RED, source=stock, view=view_inc)
    p.segment(x0='date', x1='date', y0='low', y1='high', color=GREEN, source=stock, view=view_dec)

    p.vbar(x='date', width=width, top='open', bottom='close', fill_color=RED, line_color=RED,
           source=stock,
           view=view_inc)
    p.vbar(x='date', width=width, top='open', bottom='close', fill_color=GREEN, line_color=GREEN,
           source=stock,
           view=view_dec)

    # p.line(x='date', y='close_line', line_width=1, color=BLUE, line_alpha=0.7, souce=stock)

    band = Band(base='date', lower='bolling_lower', upper='bolling_upper', source=stock, level='underlay',
                fill_alpha=0.5, line_width=1, line_color='black', fill_color=BLUE_LIGHT)
    p.add_layout(band)

    code = """
    def ticker():
        return "{:.0f} + {:.2f}".format(tick, tick % 1)
    """
    p.yaxis.formatter = NumeralTickFormatter(format='$ 0,0[.]000')

    return p


# Simple Moving Average
def plot_sma(stock):
    p = figure(x_axis_type="datetime", plot_width=WIDTH_PLOT, plot_height=300,
               title="Simple Moving Average (press the legend to hide/show lines)",
               tools=TOOLS, toolbar_location='above')

    p.line(x='date', y='SMA_5', line_width=2, color=BLUE, source=stock, legend='5 days', muted_color=BLUE,
           muted_alpha=0.2)
    p.line(x='date', y='SMA_10', line_width=2, color=ORANGE, source=stock, legend='10 days', muted_color=ORANGE,
           muted_alpha=0.2)
    p.line(x='date', y='SMA_50', line_width=2, color=PURPLE, source=stock, legend='50 days', muted_color=PURPLE,
           muted_alpha=0.2)
    p.line(x='date', y='SMA_100', line_width=2, color=BROWN, source=stock, legend='100 days', muted_color=BROWN,
           muted_alpha=0.2)

    p.legend.location = "bottom_left"
    p.legend.border_line_alpha = 0
    p.legend.background_fill_alpha = 0
    p.legend.click_policy = "mute"
    p.yaxis.formatter = NumeralTickFormatter(format='$ 0,0[.]000')

    return p


# MACD (line + histogram)
def plot_macd(stock):
    p = figure(x_axis_type="datetime", plot_width=WIDTH_PLOT, plot_height=200, title="MACD (line + histogram)",
               tools=TOOLS, toolbar_location='above')

    up = [True if val > 0 else False for val in stock.data['macd_histogram']]
    down = [True if val < 0 else False for val in stock.data['macd_histogram']]

    view_upper = CDSView(source=stock, filters=[BooleanFilter(up)])
    view_lower = CDSView(source=stock, filters=[BooleanFilter(down)])
    p.vbar(x='date', top='macd_histogram', bottom='zeros', width=30000000, color=GREEN, source=stock, view=view_upper)
    p.vbar(x='date', top='zeros', bottom='macd_histogram', width=30000000, color=RED, source=stock, view=view_lower)

    # Adding an extra range for the MACD lines, because using the same axis as the histogram
    # sometimes flattens them too much
    p.extra_y_ranges = {'macd': DataRange1d()}
    p.add_layout(LinearAxis(y_range_name='macd'), 'right')

    p.line(x='date', y='macd', line_width=2, color=BLUE, source=stock, legend='MACD', muted_color=BLUE,
           muted_alpha=0, y_range_name='macd')
    p.line(x='date', y='macd_signal', line_width=2, color=BLUE_LIGHT, source=stock, legend='Signal',
           muted_color=BLUE_LIGHT, muted_alpha=0, y_range_name='macd')

    p.legend.location = "bottom_left"
    p.legend.border_line_alpha = 0
    p.legend.background_fill_alpha = 0
    p.legend.click_policy = "mute"

    p.yaxis.ticker = []
    p.yaxis.axis_line_alpha = 0

    return p


# RSI
def plot_rsi(stock):
    p = figure(x_axis_type="datetime", plot_width=WIDTH_PLOT, plot_height=200, title="RSI 15 days",
               tools=TOOLS, toolbar_location='above')

    p.line(x='date', y='rsi_15', line_width=2, color=BLUE, source=stock)

    low_box = BoxAnnotation(top=30, fill_alpha=0.1, fill_color=RED)
    p.add_layout(low_box)
    high_box = BoxAnnotation(bottom=70, fill_alpha=0.1, fill_color=GREEN)
    p.add_layout(high_box)

    # Horizontal line
    hline = Span(location=50, dimension='width', line_color='black', line_width=0.5)
    p.renderers.extend([hline])

    p.y_range = Range1d(0, 100)
    p.yaxis.ticker = [30, 50, 70]
    p.yaxis.formatter = PrintfTickFormatter(format="%f%%")
    p.grid.grid_line_alpha = 0.3

    return p


#### On-Balance Volume (OBV)
def plot_obv(stock):
    p = figure(x_axis_type="datetime", plot_width=WIDTH_PLOT, plot_height=200, title="On-Balance Volume (OBV)",
               tools=TOOLS, toolbar_location='above')
    p.line(x='date', y='OBV', line_width=2, color=BLUE, source=stock)

    p.yaxis.ticker = []
    p.yaxis.axis_line_alpha = 0

    return p


#### Volume line
def plot_volume(stock):
    p = figure(x_axis_type="datetime", plot_width=WIDTH_PLOT, plot_height=200, title="Volume", tools=TOOLS,
               toolbar_location='above')
    p.line(x='date', y='volume', line_width=2, color=BLUE, source=stock)

    return p


#### Plot of symbols to choose TICKET
def widget_symbols():
    # Get all symbols
    all_stocks_call = 'https://api.iextrading.com/1.0/ref-data/symbols'
    response = requests.get(all_stocks_call)
    respon = response.json()

    symbols = []
    for e in respon:
        if e['type'] != 'N/A':
            symbols.append(e['symbol'])

    select_ticket = Select(value="AAPL", options=symbols)
    return select_ticket


def widget_show_text(text):
    pre = PreText(text=text, width=500, height=10)

    return pre
