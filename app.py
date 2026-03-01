"""Run the app"""
import os
from datetime import datetime

from data import get_run_data, get_summary_stats, load_run_data_from_file
from plot import generate_plots, generate_summary

from flask import Flask, render_template_string, jsonify, request
import plotly.io as pio
# Set plotly to render in browser
pio.renderers.default = "browser"

app = Flask(__name__)

CYCLE_OPTIONS = {
    "2025 Indy Marathon": {"start_date": datetime(2025, 7, 21), "end_date": datetime(2025, 11, 8)},
    "2025 NYC/Brooklyn Half Marathon": {"start_date": datetime(2025, 2, 2), "end_date": datetime(2025, 5, 17)},
    "2024 Brooklyn Half Marathon": {"start_date": datetime(2024, 1, 1), "end_date": datetime(2024, 5, 18)},
    "2022 Twin-Cities Marathon": {"start_date": datetime(2022, 5, 16), "end_date": datetime(2022, 10, 2)},
    "2021 CIM Marathon": {"start_date": datetime(2021, 6, 21), "end_date": datetime(2021, 10, 2)},
    "2020 NYC Virtual Marathon": {"start_date": datetime(2020, 8, 9), "end_date": datetime(2020, 10, 17)},
    "2019 Twin-Cities Marathon": {"start_date": datetime(2019, 7, 29), "end_date": datetime(2019, 10, 6)},
}

CYCLE_OPTIONS_LIST = [(key, key) for key in CYCLE_OPTIONS]
# Dropdown: YTD first (default), then all cycles
PLOT_OPTIONS_LIST = [("YTD", "YTD")] + CYCLE_OPTIONS_LIST
DEFAULT_PLOT_KEY = "YTD"

@app.route('/')
def home():
    """Generate the plot and summary HTML"""
    selected_cycle = request.args.get('cycle', DEFAULT_PLOT_KEY)
    valid_plot_keys = {"YTD"} | set(CYCLE_OPTIONS)
    if selected_cycle not in valid_plot_keys:
        selected_cycle = DEFAULT_PLOT_KEY

    # YTD data: read from API
    ytd_start = datetime(datetime.now().year, 1, 1)
    run_df_ytd = get_run_data(read_date=ytd_start)

    # Cycle data: read from static file (no API call)
    run_df = load_run_data_from_file()
    if not run_df.empty:
        run_df = get_run_data(df=run_df)

    cycle_data_map = {}
    empty_df = run_df.iloc[0:0].copy() if not run_df.empty else run_df.copy()

    for cycle_key, opts in CYCLE_OPTIONS.items():
        start_d, end_d = opts["start_date"], opts["end_date"]
        if run_df.empty:
            run_df_cycle = run_df.copy()
        else:
            run_df_cycle = run_df[
                (run_df["start_date_local"].dt.date >= start_d.date()) &
                (run_df["start_date_local"].dt.date <= end_d.date())
            ].copy()
        cycle_data_map[cycle_key] = run_df_cycle

    # Selected period: YTD (from API) or cycle (from file)
    if selected_cycle == "YTD":
        run_df_selected = run_df_ytd
        selected_cycle_display = f"{datetime.now().year} YTD"
    else:
        run_df_selected = cycle_data_map.get(selected_cycle, empty_df)
        selected_cycle_display = selected_cycle

    # Summary stats for the selected period
    if run_df_selected.empty:
        summary_html = '<div class="metric">No data available for this period.</div>'
    else:
        summary_html = generate_summary(get_summary_stats(run_df_selected))

    fig = generate_plots(run_df_selected)
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn') # type: ignore

    # Read the main HTML template
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Render the template with the generated HTML
    return render_template_string(
        template_content,
        plot_html=plot_html,
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        cycle_options=PLOT_OPTIONS_LIST,
        selected_cycle=selected_cycle,
        selected_cycle_display=selected_cycle_display,
        summary_html=summary_html,
    )

@app.route('/refresh')
def refresh():
    """Force refresh data and redirect to home"""
    # This endpoint can be used to manually trigger a data refresh
    return home()

@app.route('/api/status')
def status():
    """API endpoint: YTD run count and latest activity from API."""
    try:
        ytd_start = datetime(datetime.now().year, 1, 1)
        run_df = get_run_data(read_date=ytd_start)
        return jsonify({
            'status': 'success',
            'last_updated': datetime.now().isoformat(),
            'ytd_runs': len(run_df),
            'latest_activity': run_df['start_date_local'].max() if len(run_df) > 0 else None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host=host, port=port, debug=True)
