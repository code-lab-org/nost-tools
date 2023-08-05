FROM python:3.9 AS nost_runtime

WORKDIR /nost_tools
COPY pyproject.toml ./
COPY nost_tools nost_tools
RUN python -m pip install --no-cache-dir .

FROM nost_runtime AS monitor_backend

WORKDIR /monitor
COPY ./monitor/requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade -r ./requirements.txt
COPY ./monitor/backend ./backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "3000"]