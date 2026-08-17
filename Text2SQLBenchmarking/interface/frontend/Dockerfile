# syntax=docker/dockerfile:1

FROM node:24-alpine3.22 AS build

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY . ./
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.29.5-alpine

USER root
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /build/dist/ /usr/share/nginx/html/
USER 101

EXPOSE 5173
