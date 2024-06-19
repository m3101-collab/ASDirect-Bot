FROM python:3.12
WORKDIR /app
COPY ./dist/*.whl .
RUN pip install --no-cache-dir ./*.whl
CMD ["asdirect_bot"]