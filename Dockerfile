FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY hi_lo_wells/ hi_lo_wells/

RUN pip install --no-cache-dir -e .

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV HI_LO_WELLS_NO_BROWSER=1

CMD ["hi-lo-wells"]