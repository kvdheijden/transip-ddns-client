FROM python:3.7-slim

WORKDIR /usr/src/app
RUN mkdir /usr/src/data

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/usr/src/data"]
ENTRYPOINT ["python", "-m", "ddns"]
CMD ["--help"]