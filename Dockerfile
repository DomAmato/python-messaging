from python:3-alpine

WORKDIR /usr/src/app

COPY . .

RUN pip install pytest pylint

CMD ["tail", "-f", "/dev/null"]