FROM nginx:1.29.4

COPY conf/nginx.conf /etc/nginx/nginx.conf
COPY conf/conf.d/ /etc/nginx/conf.d/

COPY frontend-compiled/ /usr/share/nginx/html/