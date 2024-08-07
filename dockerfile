FROM python:3.12-slim as build
WORKDIR /build
RUN pip install --no-cache-dir build
COPY ./src/ ./src/
COPY ./pyproject.toml ./
RUN python -m build .

FROM python:3.12-slim as release
WORKDIR /app
COPY --from=build /build/dist/*.whl ./
RUN pip install --no-cache-dir ./*.whl
RUN rm *.whl
CMD ["asdirect_bot"]