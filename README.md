# Miniverse-Backend

Miniverse frontend repo : https://github.com/Louis-PAGNIER/Miniverse

## Running project :

### Prod:

#### unix
```sh
docker compose down && GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD) docker compose up --build
```

#### windows

```powershell
docker compose down; $env:GIT_BRANCH = $( git rev-parse --abbrev-ref HEAD ); docker-compose up --build
```

### Debug:
#### unix
```sh
docker compose -f docker-compose-debug.yml up -d --watch
set -a; source .env.debug;
python -m litestar --app app.main:app run --debug --host 0.0.0.0 --port 8000 
```
 
#### windows
```powershell
docker compose -f .\docker-compose-debug.yml up -d
Get-Content .env.debug | ForEach-Object { $name, $value = $_ -split '='; [Environment]::SetEnvironmentVariable($name,$value) }
python -m litestar --app app.main:app run --debug --host 0.0.0.0 --port 8000
```
