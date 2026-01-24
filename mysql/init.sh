#!/bin/bash
set -e

# Use the 'mysql' command to run SQL with variables
mysql -uroot -p"$MYSQL_ROOT_PASSWORD" <<EOSQL
  CREATE DATABASE IF NOT EXISTS miniverse_db;
  CREATE USER IF NOT EXISTS 'miniverse_db_user'@'%' IDENTIFIED BY '$MINIVERSE_DB_PASS';
  GRANT ALL PRIVILEGES ON miniverse_db.* TO 'miniverse_db_user'@'%';

  CREATE DATABASE IF NOT EXISTS keycloak_db;
  CREATE USER IF NOT EXISTS 'keycloak_db_user'@'%' IDENTIFIED BY '$KEYCLOAK_DB_PASS';
  GRANT ALL PRIVILEGES ON keycloak_db.* TO 'keycloak_db_user'@'%';

  FLUSH PRIVILEGES;
EOSQL