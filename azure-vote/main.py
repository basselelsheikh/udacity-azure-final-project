from flask import Flask, request, render_template
import os
import random
import redis
import socket
import sys
import logging
from datetime import datetime

APP_INSIGHTS_KEY = "YOUR_INSTRUMENTATION_KEY_HERE"
APP_INSIGHTS_CONN_STRING = "InstrumentationKey=c949c2c4-6566-4517-999d-5043c81d94ed;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=e8772aa2-0f98-4c0f-ba55-f0f89fb13833"

# App Insights
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.trace.samplers import AlwaysOnSampler
from opencensus.trace.tracer import Tracer

# Logging
logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string=APP_INSIGHTS_CONN_STRING))
logger.setLevel(logging.INFO)

# Metrics
exporter = metrics_exporter.new_metrics_exporter(
    enable_standard_metrics=True,
    connection_string=APP_INSIGHTS_CONN_STRING
)

# Tracing
tracer = Tracer(
    exporter=AzureExporter(connection_string=APP_INSIGHTS_CONN_STRING),
    sampler=AlwaysOnSampler()
)
app = Flask(__name__)

# Requests
middleware = FlaskMiddleware(
    app,
    exporter=AzureExporter(connection_string=APP_INSIGHTS_CONN_STRING),
    sampler=AlwaysOnSampler()
)

# Load configurations from environment or config file
app.config.from_pyfile('config_file.cfg')

if ("VOTE1VALUE" in os.environ and os.environ['VOTE1VALUE']):
    button1 = os.environ['VOTE1VALUE']
else:
    button1 = app.config['VOTE1VALUE']

if ("VOTE2VALUE" in os.environ and os.environ['VOTE2VALUE']):
    button2 = os.environ['VOTE2VALUE']
else:
    button2 = app.config['VOTE2VALUE']

if ("TITLE" in os.environ and os.environ['TITLE']):
    title = os.environ['TITLE']
else:
    title = app.config['TITLE']

# Redis Connection
r = redis.Redis()

# Change title to host name to demo NLB
if app.config['SHOWHOST'] == "true":
    title = socket.gethostname()

# Init Redis
if not r.get(button1): r.set(button1,0)
if not r.get(button2): r.set(button2,0)

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'GET':

        # Get current values
        vote1 = r.get(button1).decode('utf-8')
        with tracer.span(name="Cats Vote GET"):
            pass
        
        vote2 = r.get(button2).decode('utf-8')
        with tracer.span(name="Dogs Vote GET"):
            pass

        # Return index with values
        return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

    elif request.method == 'POST':

        if request.form['vote'] == 'reset':

            # Empty table and return results
            r.set(button1,0)
            r.set(button2,0)
            vote1 = r.get(button1).decode('utf-8')
            properties = {'custom_dimensions': {'Cats Vote': vote1}}
            logger.info('Cats vote reset.', extra=properties)

            vote2 = r.get(button2).decode('utf-8')
            properties = {'custom_dimensions': {'Dogs Vote': vote2}}
            logger.info('Dogs vote reset.', extra=properties)

            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

        else:

            # Insert vote result into DB
            vote = request.form['vote']
            r.incr(vote,1)

            with tracer.span(name=f"Vote Recorded: {vote}"):
                pass

            properties = {'custom_dimensions': {'Voted For': vote}}
            logger.warning(f'{vote} button was clicked.', extra=properties)

            # Get current values
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')

            # Return results
            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

if __name__ == "__main__":
    # app.run() 
    app.run(host='0.0.0.0', threaded=True, debug=True) # remote
