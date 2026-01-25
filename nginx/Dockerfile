FROM node:25-alpine3.22 AS builder

RUN apk add --no-cache git

WORKDIR /html

ARG REPO_URL=https://github.com/Louis-PAGNIER/Miniverse
ARG BRANCH=main

RUN git clone -b ${BRANCH} ${REPO_URL} .

RUN npm install
RUN npm run build

FROM quay.io/keycloak/keycloak:26.5.0


FROM nginx:1.29.4

COPY conf/nginx.conf /etc/nginx/nginx.conf
COPY conf/conf.d/ /etc/nginx/conf.d/

COPY --from=builder /html/dist/ /usr/share/nginx/html/