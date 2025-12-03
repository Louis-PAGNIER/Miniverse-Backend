# Miniverse-Backend

## Running project :

### Prod:
```sh
docker compose up
```

### Debug:
#### unix
```sh
docker compose -f docker-compose-debug.yml up -d
set -a; source .env.debug;
python -m litestar --app app.main:app run --debug --host 0.0.0.0 --port 8000 
```
 
#### windows
```powershell
docker compose -f .\docker-compose-debug.yml up -d
Get-Content .env.debug | ForEach-Object { $name, $value = $_ -split '='; [Environment]::SetEnvironmentVariable($name,$value) }
python -m litestar --app app.main:app run --debug --host 0.0.0.0 --port 8000
```
