FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY open_wells/ open_wells/

RUN pip install --no-cache-dir -e .

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV OPEN_WELLS_NO_BROWSER=1

CMD ["open-wells"]