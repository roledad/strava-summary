"""Run the app"""

from data import get_run_data, get_summary_stats
from plot import generate_plots, generate_summary

from flask import Flask, render_template_string
import plotly.io as pio
# Set plotly to render in browser
pio.renderers.default = "browser"

run_df = get_run_data()
summary_stats = get_summary_stats(run_df)

app = Flask(__name__)

@app.route('/')
def home():
    """Generate the plot and summary HTML"""
    summary_html = generate_summary(summary_stats)
    fig = generate_plots(run_df)
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn') # type: ignore

    # Read the main HTML template
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Render the template with the generated HTML
    return render_template_string(
        template_content,
        summary_html=summary_html,
        plot_html=plot_html
    )

if __name__ == '__main__':
    app.run(debug=True)
