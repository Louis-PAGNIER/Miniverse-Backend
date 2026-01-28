FROM nginx:1.29.4-alpine AS nginx-builder

ARG NGINX_VERSION=1.29.4

RUN apk add --no-cache \
    git \
    gcc \
    make \
    pcre2-dev \
    zlib-dev \
    zstd-dev \
    openssl-dev \
    alpine-sdk \
    wget

# Download Nginx source code (must match the version of the base image)
RUN wget http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz && \
    tar -xzvf nginx-${NGINX_VERSION}.tar.gz

# Clone the mod_zip repository
RUN git clone https://github.com/evanmiller/mod_zip.git
RUN git clone https://github.com/fdintino/nginx-upload-module.git
RUN git clone https://github.com/tokers/zstd-nginx-module


# Compile Nginx with the module
WORKDIR /nginx-${NGINX_VERSION}
RUN ./configure --with-compat \
    --add-dynamic-module=/mod_zip \
    --add-dynamic-module=/nginx-upload-module \
    --add-dynamic-module=/zstd-nginx-module \
    && make modules

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

# Set uid:gid to 1000:1000 to match backend perms
RUN apk add --no-cache  \
    openssl  \
    zstd \
    shadow && usermod -u 1000 nginx && groupmod -g 1000 nginx && apk del shadow


COPY --from=nginx-builder /nginx-*/objs/ngx_http_zip_module.so /usr/lib/nginx/modules/
COPY --from=nginx-builder /nginx-*/objs/ngx_http_upload_module.so /usr/lib/nginx/modules/
COPY --from=nginx-builder /nginx-*/objs/ngx_http_zstd_filter_module.so /usr/lib/nginx/modules/
COPY --from=nginx-builder /nginx-*/objs/ngx_http_zstd_static_module.so /usr/lib/nginx/modules/

COPY conf/nginx.conf /etc/nginx/nginx.conf
COPY conf/conf.d/ /etc/nginx/conf.d/

COPY entrypoint.sh /docker-entrypoint.d/99-generate-cert.sh
RUN chmod +x /docker-entrypoint.d/99-generate-cert.sh

COPY --from=frontend-builder /html/dist/ /usr/share/nginx/html/

# Pre-compress frontend files
RUN find /usr/share/nginx/html/ -type f -not -name "*.zst" -exec zstd -22 --ultra {} +

EXPOSE 443/tcp
# Redirect 80 to 443
EXPOSE 80/tcp