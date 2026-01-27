FROM nginx:1.29.4-alpine AS nginx-builder

ARG NGINX_VERSION=1.29.4

RUN apk add --no-cache --virtual \
    openssl \
    git \
    gcc \
    libc-dev \
    make \
    openssl-dev \
    pcre2-dev \
    zlib-dev \
    linux-headers \
    libxslt-dev \
    gd-dev \
    geoip-dev \
    libedit-dev \
    bash \
    alpine-sdk \
    findutils \
    curl \
    cargo \
    clang-libclang

# Download Nginx source code (must match the version of the base image)
RUN wget http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz && \
    tar -xzvf nginx-${NGINX_VERSION}.tar.gz

# Clone the mod_zip repository
RUN git clone https://github.com/evanmiller/mod_zip.git
RUN git clone https://github.com/fdintino/nginx-upload-module.git

# Compile Nginx with the module
WORKDIR /nginx-${NGINX_VERSION}
RUN ./configure --prefix=/etc/nginx  \
    --sbin-path=/usr/sbin/nginx  \
    --modules-path=/usr/lib/nginx/modules  \
    --conf-path=/etc/nginx/nginx.conf  \
    --error-log-path=/var/log/nginx/error.log  \
    --http-log-path=/var/log/nginx/access.log  \
    --pid-path=/run/nginx.pid  \
    --lock-path=/run/nginx.lock  \
    --http-client-body-temp-path=/var/cache/nginx/client_temp  \
    --http-proxy-temp-path=/var/cache/nginx/proxy_temp  \
    --http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp  \
    --http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp  \
    --http-scgi-temp-path=/var/cache/nginx/scgi_temp  \
    --user=nginx  \
    --group=nginx  \
    --with-compat  \
    --with-file-aio  \
    --with-threads  \
    --with-http_addition_module  \
    --with-http_auth_request_module  \
    --with-http_dav_module  \
    --with-http_flv_module  \
    --with-http_gunzip_module  \
    --with-http_gzip_static_module  \
    --with-http_mp4_module  \
    --with-http_random_index_module  \
    --with-http_realip_module  \
    --with-http_secure_link_module  \
    --with-http_slice_module  \
    --with-http_ssl_module  \
    --with-http_stub_status_module  \
    --with-http_sub_module  \
    --with-http_v2_module  \
    --with-http_v3_module  \
    --with-mail \
    --with-mail_ssl_module \
    --with-stream \
    --with-stream_realip_module  \
    --with-stream_ssl_module \
    --with-stream_ssl_preread_module \
    --with-cc-opt='-g -O2 -Werror=implicit-function-declaration -ffile-prefix-map=/home/builder/debuild/nginx-1.29.4/debian/debuild-base/nginx-1.29.4=. -fstack-protector-strong -fstack-clash-protection -Wformat -Werror=format-security -fcf-protection -Wp,-D_FORTIFY_SOURCE=2 -fPIC' \
    --with-ld-opt='-Wl,-z,relro -Wl,-z,now -Wl,--as-needed -pie' \
    --add-module=../mod_zip \
    --add-module=../nginx-upload-module && \
    make build

FROM node:25.5.0 AS frontend-builder

# Importing frontend from git
WORKDIR /html

ARG REPO_URL=https://github.com/Louis-PAGNIER/Miniverse
ARG BRANCH=main

ADD https://api.github.com/repos/Louis-PAGNIER/Miniverse/commits/${BRANCH} /dev/null

RUN git clone --depth 1 --single-branch -b ${BRANCH} ${REPO_URL} .

RUN npm install
RUN npm run build

# Nginx version must match ${NGINX_VERSION} declared above
FROM nginx:1.29.4-alpine

RUN apk add --no-cache openssl

COPY --from=nginx-builder /nginx-*/objs/nginx /usr/sbin/nginx

COPY conf/nginx.conf /etc/nginx/nginx.conf
COPY conf/conf.d/ /etc/nginx/conf.d/

COPY entrypoint.sh /docker-entrypoint.d/99-generate-cert.sh
RUN chmod +x /docker-entrypoint.d/99-generate-cert.sh

COPY --from=frontend-builder /html/dist/ /usr/share/nginx/html/

EXPOSE 443/tcp
# Redirect 80 to 443
EXPOSE 80/tcp