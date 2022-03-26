
FROM python:3.9-bullseye

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
  # Cryptography dependencies (for esptool 3.0)
  && apt-get install -y libssl-dev libffi-dev \
  # pyzmq dependencies
  && apt-get install -y libzmq3-dev \
  # Git for updates, avrdude for flashing arduinos, ssh/curl for accessing sites, cron for maintaining circus
  && apt-get install -y git-core avrdude ssh curl \
  # nano so that I can edit files easily inside the container while testing
  # (I am not a fan of vim. sorry.)
  # TODO - Remove this
  && apt-get install -y nano \
  # all the bluetooth libs
  && apt-get install -y bluez libcap2-bin libbluetooth3 libbluetooth-dev \
  # We need avahi-utils and libnss-mdns for mDNS support
  && apt-get install -y avahi-utils libnss-mdns \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*


RUN addgroup --system django \
    && adduser --system --ingroup django django

# Add piwheels (and our custom wheels!) to pip.conf for the armv7 scipy/numpy builds
COPY ./compose/production/django/pip.conf /etc/pip.conf

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install --no-cache-dir -r /requirements/docker-production.txt

COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

# Fix mDNS resolution
COPY ./compose/production/django/nsswitch.conf /etc/nsswitch.conf

COPY --chown=django:django ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY ./compose/production/django/daemons/huey/start /start-huey
RUN sed -i 's/\r$//g' /start-huey
RUN chmod +x /start-huey

COPY --chown=django:django . /app

# Add the django user to the container's dialout group
RUN usermod -a -G dialout django

# Correct the permissions for /app/data and /app/log
RUN chown django /app/data/
RUN chown django /app/log/

# Fix Bluetooth permissions
RUN setcap cap_net_raw,cap_net_admin+eip /usr/local/bin/python3.9

USER django

RUN cd /app && git remote set-url origin https://www.github.com/thorrak/fermentrack.git

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
