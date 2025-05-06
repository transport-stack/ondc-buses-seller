# https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/


###########
# BUILDER #
###########

# pull official base image
FROM python:3.8.19 as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apt update \
    && apt install -y libpq-dev gcc python3-dev

RUN pip install --upgrade pip

# install dependencies
COPY ./requirements*.txt .
RUN for reqs in /usr/src/app/requirements*.txt; do pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r $reqs; done
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels gunicorn


#########
# FINAL #
#########

# pull official base image
FROM python:3.8.19
ENV TZ="Asia/Kolkata"

# create the appropriate directories
ENV APP_HOME=/usr/src/app
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# install dependencies
RUN apt update && apt install -y libpq-dev
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements*.txt .
RUN pip install --no-cache /wheels/*

# copy project
COPY . $APP_HOME

RUN chmod +x /usr/src/app/entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
