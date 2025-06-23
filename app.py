"""
Run the app
"""

from flask import Flask, render_template_string

# Import your plotting function
from plot import generate_plots

app = Flask(__name__)

@app.route('/')
def home():
    """Generate the plot and summary HTML"""
    summary_html, plot_html = generate_plots()

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
