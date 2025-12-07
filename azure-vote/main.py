from flask import Flask, request, render_template
import os
import redis
import socket
import logging

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

APP_INSIGHTS_KEY = "86dff2e7-9c85-4a73-acbc-e35a19065cee"

app = Flask(__name__)
app.config.from_pyfile('config_file.cfg')

button1 = os.environ.get('VOTE1VALUE', app.config['VOTE1VALUE'])
button2 = os.environ.get('VOTE2VALUE', app.config['VOTE2VALUE'])
title = os.environ.get('TITLE', app.config['TITLE'])

if app.config.get('SHOWHOST', 'false') == "true":
    title = socket.gethostname()

r = redis.Redis()
if not r.get(button1): r.set(button1, 0)
if not r.get(button2): r.set(button2, 0)

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string=f'InstrumentationKey={APP_INSIGHTS_KEY}'))
logger.setLevel(logging.INFO)

exporter = metrics_exporter.new_metrics_exporter(
    enable_standard_metrics=True,
    connection_string=f'InstrumentationKey={APP_INSIGHTS_KEY}'
)

tracer = Tracer(
    exporter=AzureExporter(connection_string=f'InstrumentationKey={APP_INSIGHTS_KEY}'),
    sampler=ProbabilitySampler(1.0)
)

middleware = FlaskMiddleware(
    app,
    exporter=AzureExporter(connection_string=f'InstrumentationKey={APP_INSIGHTS_KEY}'),
    sampler=ProbabilitySampler(1.0)
)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        vote1 = r.get(button1).decode('utf-8')
        with tracer.span(name="Cats Vote GET"):
            pass
        vote2 = r.get(button2).decode('utf-8')
        with tracer.span(name="Dogs Vote GET"):
            pass

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

            logger.info('Cats vote reset', extra={"custom_dimensions": {"Cats Vote": vote1}})
            logger.info('Dogs vote reset', extra={"custom_dimensions": {"Dogs Vote": vote2}})

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

            logger.info(f'{vote} vote clicked', extra={"custom_dimensions": {"Voted For": vote}})

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