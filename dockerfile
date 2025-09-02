FROM python:3.13 AS deps

RUN apt update -y && apt upgrade -y --no-install-recommends && apt clean

WORKDIR                     /dalia
COPY   ./requirements.txt   /dalia/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
RUN apt install -y net-tools

FROM deps

WORKDIR /dalia
COPY ./ /dalia

CMD ["python", "main.py"]