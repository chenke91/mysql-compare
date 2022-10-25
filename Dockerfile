FROM chenke91/mysql-compare-base
COPY ./compare.py /data/
ENTRYPOINT ["python", "/data/compare.py"]