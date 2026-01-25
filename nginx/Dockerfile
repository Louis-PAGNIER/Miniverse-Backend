FROM node:25-alpine3.22 AS builder

RUN apk add --no-cache git

WORKDIR /html

ARG REPO_URL=https://github.com/Louis-PAGNIER/Miniverse
ARG BRANCH=main

ADD https://api.github.com/repos/Louis-PAGNIER/Miniverse/commits/${BRANCH} /dev/null

RUN git clone --depth 1 --single-branch -b ${BRANCH} ${REPO_URL} .

RUN npm install
RUN npm run build

FROM nginx:1.29.4-alpine

RUN apk add --no-cache openssl

COPY conf/nginx.conf /etc/nginx/nginx.conf
COPY conf/conf.d/ /etc/nginx/conf.d/

COPY entrypoint.sh /docker-entrypoint.d/99-generate-cert.sh
RUN chmod +x /docker-entrypoint.d/99-generate-cert.sh

COPY --from=builder /html/dist/ /usr/share/nginx/html/

EXPOSE 443/tcp
# Redirect 80 to 443
EXPOSE 80/tcp