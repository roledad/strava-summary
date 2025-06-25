"""Run the app"""

from data import get_run_data, get_summary_stats
from plot import generate_plots, generate_summary

from flask import Flask, render_template_string, jsonify
import plotly.io as pio
import os
from datetime import datetime
# Set plotly to render in browser
pio.renderers.default = "browser"

app = Flask(__name__)

@app.route('/')
def home():
    """Generate the plot and summary HTML"""
    # Reload data on each request to get latest activities
    run_df = get_run_data()
    summary_stats = get_summary_stats(run_df)

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
        plot_html=plot_html,
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
