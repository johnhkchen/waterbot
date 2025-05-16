venv:
    uv venv

activate:
    source .venv/bin/activate

sync:
    uv sync

start:
    uv run src/app/main.py

up:
    dagger -c "build | as-service | up --ports=5001:5001"

test:
    uv run pytest -v

e2e:
    dagger -c "test"
