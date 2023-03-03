# serve-app-backend

## Quickstart

Install necessary libraries and run `python main.py` or `uvicorn main:app`

## Tests

Run `pytest app/test/`

To test manually use Insomnia and provided config `Insomnia.json`
[Insomnia Import](https://docs.insomnia.rest/insomnia/import-export-data)

## Deployment
Build image via `docker build -f  ./.docker/Dockerfile . -t serve` from project root
Run `docker run -p 443:443 serve`
### Alternative Deployment
additionally to docker engine, install [Docker-Compose](https://docs.docker.com/compose/install/)
In order to start container, from root folder run: `docker-compose up -d`, where `-d` means it starts detached.
To read the logs, run `docker-compose logs -f`, where `-f` is optional and shows whole log in real time


## Development
- Create virtual env `python3 -m venv env`
- and activate it `source venv/bin/activate` (different activate scripts for various cmds available)
- Confirm usage `which python`
- install deps `pip install .docker/requirements.txt`

Run either via CLI or IDE of choice


