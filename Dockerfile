ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-slim

WORKDIR /usr/src/app
RUN mkdir /etc/transipddnsclient/

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/etc/transipddnsclient/"]
ENTRYPOINT ["python", "-m", "transipddnsclient"]
CMD ["--help"]