uv run uvicorn receiver:app --app-dir receiver --port 8080
uv run uvicorn storage:app --app-dir storage --port 8090

docker compose exec -it db mysql -u walkr_user -p walkr_db

docker compose exec receiver curl -X POST http://storage:8090/reset

docker compose exec receiver curl -s http://storage:8090/status