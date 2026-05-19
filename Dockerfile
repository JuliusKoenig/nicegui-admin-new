FROM python:3.14-bookworm

# copy library and install
COPY src /app/src
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
WORKDIR /app
RUN pip install -e .

# copy extensions and install
COPY extensions /app/extensions
WORKDIR /app/extensions/nicegui-admin_mailing
RUN pip install -e .

# copy example app and set workdir
COPY examples /examples
WORKDIR /examples

# run example app
CMD ["python", "main.py", "worker"]



