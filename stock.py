from flask import Flask, render_template, request
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
from pandas_datareader import data
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.models import HoverTool, ColumnDataSource, Label
from datetime import datetime as dt

app = Flask(__name__)


def duration(time):
    if time == "one_month":
        if (dt.now().month - 1) < 0:
            start = dt(dt.now().year - 1, (dt.now().month -1)%12, dt.now().day)
        else:
            start = dt(dt.now().year, (dt.now().month -1)%12, dt.now().day)
        val = 1
    elif time == "three_month":
        if (dt.now().month - 3) < 0:
            start = dt(dt.now().year - 1, (dt.now().month -3)%12, dt.now().day)
        else:
            start = dt(dt.now().year, (dt.now().month -3)%12, dt.now().day)
        val = 3
    elif time == "six_month":
        if (dt.now().month - 6) < 0:
            start = dt(dt.now().year - 1, (dt.now().month -6)%12, dt.now().day)
        else:
            start = dt(dt.now().year, (dt.now().month -6)%12, dt.now().day)
        val = 6
    elif time == "twelve_month":
        start = dt(dt.now().year - 1, dt.now().month, dt.now().day)
        val = 12

    return val, start


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analysis-graph", methods = ['POST'])
def graph():
    global df
    if request.method == 'POST':
        try:
            symbol = request.form["ticker"]
            time = request.form.get('time_dur')
            chart = request.form.get('chart_type')

            val, start = duration(time)

            end = dt(dt.now().year, dt.now().month, dt.now().day)

            df = data.DataReader(name = symbol, data_source = "iex", start = start, end = end)

            def inc_dec(c,o):
                if c > o:
                    value = "Increase"
                elif c < o:
                    value = "Decrease"
                else:
                    value = "Equal"
                return value

            df["status"] = [inc_dec(c,o) for c,o in zip(df.close,df.open)]
            df["middle"] = (df.open + df.close)/2
            df["height"] = abs(df.close - df.open)

            highest = max(df.close)
            lowest = min(df.close)

            p = figure(x_axis_type = 'datetime', plot_width = 1600, plot_height = 500, background_fill_color = "#00004d", sizing_mode = "scale_both", toolbar_location="above")
            p.title.text = symbol+" Chart"
            p.grid.grid_line_alpha = 0.3
            hours_12 = 12*60*60*1000


            df.index = pd.to_datetime(df.index)
            cds = ColumnDataSource(data = dict(x = df.index, y0 = df.high, y1 = df.low, volume = df.volume, c0 = df.close))

            hover = HoverTool(tooltips = [("Peak","@y0"),("Volume","@volume")], names = ["seg"])
            p.add_tools(hover)

            if chart == "candle":
                p.segment(x0 = 'x', y0 = 'y0', x1 = 'x', y1 = 'y1', color = "white",name = "seg",source = cds)
                p.rect(df.index[df.status == "Increase"], df.middle[df.status == "Increase"], hours_12,
                df.height[df.status == "Increase"], fill_color = "#00e673", line_color = "black")
                p.rect(df.index[df.status == "Decrease"], df.middle[df.status == "Decrease"], hours_12,
                df.height[df.status == "Decrease"], fill_color = "#ff0066", line_color = "black")

            elif chart == "line":
                p.line(x = 'x', y = 'c0', color = "green", line_width = 2, name = "seg", source = cds)

            high_label = Label(x = df.index[df.close == highest][0] , y = highest, x_offset = 5, y_offset = -5, text = "H",
            text_color = "white", text_font_size = "10pt", text_font_style = "bold")
            low_label = Label(x = df.index[df.close == lowest][0], y = lowest, text = "L",
            text_color = "white", text_font_size = "10pt", text_font_style = "bold")
            p.add_layout(high_label)
            p.add_layout(low_label)

            script1, div1 = components(p)

            cdn_js = CDN.js_files[0]
            cdn_css = CDN.css_files[0]

            return render_template("index.html", script1 = script1, div1 = div1, cdn_css = cdn_css, cdn_js = cdn_js,
            day_low = round(df.low[-1],2), day_high = round(df.high[-1],2), month_low = round(min(df.low),2),
            month_high = round(max(df.high),2), return_month = round(((df.close[-1] - df.close[0])/df.close[0])*100,2),
            moving_avg = round(df.close.mean(),2), extra = "info.html", val = val)

        except:
            return render_template("index.html", text = "Please enter a valid IEX ticker.")



if __name__ == "__main__":
    app.run(debug = True)
