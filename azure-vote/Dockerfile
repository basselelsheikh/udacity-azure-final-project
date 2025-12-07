FROM tiangolo/uwsgi-nginx-flask:python3.12

RUN pip install --no-cache-dir redis==5.0.1
RUN pip install --no-cache-dir opencensus==0.11.4
RUN pip install --no-cache-dir opencensus-ext-azure==1.1.13
RUN pip install --no-cache-dir opencensus-ext-flask==0.8.1
RUN pip install --no-cache-dir opencensus-ext-logging==0.1.1
RUN pip install --no-cache-dir opencensus-ext-requests==0.8.0

RUN pip install --no-cache-dir Flask==2.3.3
RUN pip install --no-cache-dir Werkzeug==2.3.7

ADD . /app