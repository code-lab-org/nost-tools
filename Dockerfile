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

FROM node AS monitor_frontend

WORKDIR /usr/src/app
COPY ./monitor/frontend/ .

RUN npm install node-sass@latest
RUN npm install sass-loader@latest
RUN npm install
RUN npm install serve -g
RUN npm rebuild node-sass
RUN npm run docker

EXPOSE 8000
CMD ["serve", "-s", "dist", "-l", "8000"]
