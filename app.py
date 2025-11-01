"""Run the app"""

from data import get_run_data, get_summary_stats
from plot import generate_plots, generate_summary

from flask import Flask, render_template_string, jsonify, request
import plotly.io as pio
import os
from datetime import datetime
# Set plotly to render in browser
pio.renderers.default = "browser"

app = Flask(__name__)

MONTH_OPTIONS = [
    ("july", "July"),
    ("august", "August"),
    ("september", "September"),
    ("october", "October"),
]
MONTH_TO_NUMBER = {key: idx for idx, (key, _) in enumerate(MONTH_OPTIONS, start=7)}
DEFAULT_MONTH_KEY = MONTH_OPTIONS[-1][0]

@app.route('/')
def home():
    """Generate the plot and summary HTML"""
    selected_month = request.args.get('month', DEFAULT_MONTH_KEY).lower()
    if selected_month not in MONTH_TO_NUMBER:
        selected_month = DEFAULT_MONTH_KEY

    # Determine the data year to fetch (use previous year if current month < July)
    now = datetime.now()
    min_month_number = min(MONTH_TO_NUMBER.values())
    data_year = now.year if now.month >= min_month_number else now.year - 1

    # Reload data on each request to get latest activities
    read_date = datetime(data_year, min_month_number, 1)
    run_df = get_run_data(read_date)

    month_label_map = dict(MONTH_OPTIONS)
    month_data_map = {}
    summary_sections = []

    for month_key, month_label in MONTH_OPTIONS:
        month_number = MONTH_TO_NUMBER[month_key]
        run_df_month = run_df[
            (run_df['start_date_local'].dt.month == month_number) &
            (run_df['start_date_local'].dt.year == data_year)
        ].copy()

        month_data_map[month_key] = run_df_month

        if run_df_month.empty:
            month_summary_html = '<div class="metric">No data available for this month.</div>'
        else:
            summary_stats = get_summary_stats(run_df_month)
            month_summary_html = generate_summary(summary_stats)

        summary_sections.append({
            'key': month_key,
            'label': f"{month_label} {data_year}",
            'html': month_summary_html
        })

    run_df_selected = month_data_map.get(selected_month, run_df.iloc[0:0])

    fig = generate_plots(run_df_selected)
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn') # type: ignore

    selected_month_display = f"{month_label_map[selected_month]} {data_year}"

    # Read the main HTML template
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Render the template with the generated HTML
    return render_template_string(
        template_content,
        summary_sections=summary_sections,
        plot_html=plot_html,
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        month_options=MONTH_OPTIONS,
        selected_month=selected_month,
        selected_month_display=selected_month_display
    )

@app.route('/refresh')
def refresh():
    """Force refresh data and redirect to home"""
    # This endpoint can be used to manually trigger a data refresh
    return home()

@app.route('/api/status')
def status():
    """API endpoint to check if new data is available"""
    try:
        run_df = get_run_data()
        return jsonify({
            'status': 'success',
            'last_updated': datetime.now().isoformat(),
            'data_points': len(run_df),
            'latest_activity': run_df['start_date_local'].max() if len(run_df) > 0 else None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host=host, port=port, debug=True)
