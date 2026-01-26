FROM node:25-bullseye AS builder

ARG NGINX_VERSION=1.29.4

RUN apt-get update && apt-get install -y \
    git \
    gcc \
    make \
    libpcre3-dev \
    zlib1g-dev \
    libssl-dev \
    wget

# Download Nginx source code (must match the version of the base image)
RUN wget http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz && \
    tar -xzvf nginx-${NGINX_VERSION}.tar.gz

# Clone the mod_zip repository
RUN git clone https://github.com/evanmiller/mod_zip.git

# Compile Nginx with the module
WORKDIR /nginx-${NGINX_VERSION}
RUN ./configure --with-compat --add-dynamic-module=/mod_zip && \
    make modules


# ------------
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

COPY --from=builder /nginx-*/objs/ngx_http_zip_module.so /usr/lib/nginx/modules/

COPY conf/nginx.conf /etc/nginx/nginx.conf
COPY conf/conf.d/ /etc/nginx/conf.d/

COPY entrypoint.sh /docker-entrypoint.d/99-generate-cert.sh
RUN chmod +x /docker-entrypoint.d/99-generate-cert.sh

COPY --from=builder /html/dist/ /usr/share/nginx/html/

EXPOSE 443/tcp
# Redirect 80 to 443
EXPOSE 80/tcp