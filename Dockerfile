FROM python:alpine3.16
COPY ./compare.py /data/
COPY ./requirements.txt /data/
RUN pip install -r /data/requirements.txt
CMD ["python", "/data/compare.py"]