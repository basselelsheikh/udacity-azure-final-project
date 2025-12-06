from flask import Flask, request, render_template
import os
import redis
import socket
import logging

# ===========================
# TODO: Import required libraries for App Insights
# ===========================
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.metrics_exporter import new_metrics_exporter
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import AlwaysOnSampler
from opencensus.trace.tracer import Tracer
from opencensus.ext.azure.common import telemetry

APP_INSIGHTS_CONN_STRING = "InstrumentationKey=c949c2c4-6566-4517-999d-5043c81d94ed;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=e8772aa2-0f98-4c0f-ba55-f0f89fb13833"

app = Flask(__name__)
app.config.from_pyfile('config_file.cfg')

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string=APP_INSIGHTS_CONN_STRING))
logger.setLevel(logging.INFO)

metrics = new_metrics_exporter(
    enable_standard_metrics=True,
    connection_string=APP_INSIGHTS_CONN_STRING
)

tracer = Tracer(
    exporter=AzureExporter(connection_string=APP_INSIGHTS_CONN_STRING),
    sampler=AlwaysOnSampler()
)

middleware = FlaskMiddleware(
    app,
    exporter=AzureExporter(connection_string=APP_INSIGHTS_CONN_STRING),
    sampler=AlwaysOnSampler()
)

button1 = os.environ.get('VOTE1VALUE', app.config['VOTE1VALUE'])
button2 = os.environ.get('VOTE2VALUE', app.config['VOTE2VALUE'])
title = os.environ.get('TITLE', app.config['TITLE'])

if app.config.get('SHOWHOST', 'false') == "true":
    title = socket.gethostname()

r = redis.Redis()
if not r.get(button1):
    r.set(button1, 0)
if not r.get(button2):
    r.set(button2, 0)

event_exporter = AzureExporter(connection_string=APP_INSIGHTS_CONN_STRING)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        vote1 = r.get(button1).decode('utf-8')
        vote2 = r.get(button2).decode('utf-8')
        return render_template(
            "index.html",
            value1=int(vote1),
            value2=int(vote2),
            button1=button1,
            button2=button2,
            title=title
        )

    elif request.method == 'POST':
        vote = request.form['vote']

        if vote == 'reset':
            r.set(button1, 0)
            r.set(button2, 0)

            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')

            logger.info('Cats vote reset.', extra={"custom_dimensions": {"Cats Vote": vote1}})
            logger.info('Dogs vote reset.', extra={"custom_dimensions": {"Dogs Vote": vote2}})

            return render_template(
                "index.html",
                value1=int(vote1),
                value2=int(vote2),
                button1=button1,
                button2=button2,
                title=title
            )

        else:
            r.incr(vote, 1)

            with tracer.span(name=f"Vote Recorded: {vote}"):
                pass

            logger.info(f"{vote} vote recorded.", extra={"custom_dimensions": {"Voted For": vote}})

            event = telemetry.Event(
                name=f"{vote}Clicked",
                properties={"vote": vote}
            )
            event_exporter.export([event])

            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')

            return render_template(
                "index.html",
                value1=int(vote1),
                value2=int(vote2),
                button1=button1,
                button2=button2,
                title=title
            )

if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=True, debug=True)