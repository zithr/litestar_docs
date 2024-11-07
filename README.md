Litestar server providing endpoint to upload a file, returning a zip file containing .docx files pre-populated with information given in uploaded file. No data is saved on the server.

## Pre-requisites

- Python
    - Poetry

## Setup

`poetry install`

## Run server

`poetry run python src/app.py` or `docker compose up`

## Ansible

Server can be deployed on a remote machine via Ansible. You will need to modify parts of the playbook, and inventory files for hosts and secrets with your host machine information.

`ansible-playbook ansible/service_litestar/litestar_setup.yml -i ansible/service_litestar/hosts -i path/to/secrets/file`