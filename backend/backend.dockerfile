FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install aiohttp PyMuPDF celery~=4.3 passlib[bcrypt] tenacity boto3 python-jose requests emails pydantic fastapi uvicorn gunicorn pyjwt python-multipart email_validator jinja2 psycopg2-binary alembic SQLAlchemy

# For development, Jupyter remote kernel, Hydrogen
# Using inside the container:
# jupyter notebook --ip=0.0.0.0 --allow-root
ARG env=prod
RUN bash -c "if [ $env == 'dev' ] ; then pip install jupyter ; fi"
EXPOSE 8888

COPY ./app /app
WORKDIR /app/

ENV PYTHONPATH=/app

EXPOSE 80


pip install mypy black isort autoflake flake8 pytest sqlalchemy-stubs pytest-cov