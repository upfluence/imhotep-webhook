FROM alpine:3.4
MAINTAINER Alexis Montagne <alexis.montagne@gmail.com>

ADD . /app

WORKDIR /app

RUN apk update && apk add build-base bash curl ca-certificates git openssh \
  bzip2 python go python-dev ruby ruby-dev ruby-io-console ruby-bigdecimal \
  ruby-json nodejs && \
  go get -u github.com/golang/lint/golint && \
  npm install -g eslint eslint-plugin-ember-suave && \
  ln -s /usr/include/ruby2.3.1 /usr/include/ruby && \
  echo 'gem: --no-rdoc --no-ri' >> /etc/gemrc && \
  gem install rake bundler rubocop && \
  ln -sf /usr/bin/python2.7 /usr/bin/python && \
  curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python && \
  pip install -r requirements.txt

CMD  gunicorn app:app -b 0.0.0.0:5000 -t 600
