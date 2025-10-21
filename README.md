# Miniverse-Backend

## Running project :

### Prod:
```sh
docker compose up
```

### Debug:
#### unix
```sh
set -a; source .env.debug;
docker compose -f .\docker-compose-debug.yml up -d
python -m litestar --app app.main:app run --debug --host 0.0.0.0 --port 8000 
```
 
#### windows
```powershell
Get-Content .env.debug | ForEach-Object { $name, $value = $_ -split '='; [Environment]::SetEnvironmentVariable($name,$value) }
docker compose -f .\docker-compose-debug.yml up -d
python -m litestar --app app.main:app run --debug --host 0.0.0.0 --port 8000
```
