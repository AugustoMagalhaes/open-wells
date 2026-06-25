FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY omni_wells/ omni_wells/

RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV OMNI_WELLS_NO_BROWSER=1

CMD ["omni-wells"]