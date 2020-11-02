
FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # Pillow dependencies
  && apt-get install -y libjpeg62 zlib1g libtiff5 libfreetype6 libjpeg62-turbo-dev zlib1g-dev libtiff5-dev libfreetype6-dev \
  # Other things which Fermentrack might benefit from
  && apt-get install -y git-core avrdude ssh curl \
  # Currently, installing scipy/numpy installs Python3.7
  # TODO - Figure this out
  #&& apt-get install -y python3-scipy python3-numpy \
  && apt-get install -y bluez libcap2-bin libbluetooth3 libbluetooth-dev \
  # We need avahi-utils and libnss-mdns for mDNS support
  && apt-get install -y avahi-utils libnss-mdns \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*


RUN addgroup --system django \
    && adduser --system --ingroup django django

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install --no-cache-dir -r /requirements/docker-production.txt \
    && rm -rf /requirements

COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

# Fix mDNS resolution
COPY ./compose/production/django/nsswitch.conf /etc/nsswitch.conf

COPY --chown=django:django ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY --chown=django:django . /app

# Correct the permissions for /app/data
RUN chown django /app/data/

USER django

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
