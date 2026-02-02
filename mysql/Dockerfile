FROM mysql:9.5.0

# Copy the shell script instead of the SQL file
COPY init.sh /docker-entrypoint-initdb.d/

# Ensure the script has execution permissions
RUN dos2unix /docker-entrypoint-initdb.d/init.sh && chmod +x /docker-entrypoint-initdb.d/init.sh