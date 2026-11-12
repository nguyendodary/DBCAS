FROM node:24-alpine AS build
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_LOCAL_MAILBOX_URL=""
ENV VITE_LOCAL_MAILBOX_URL=$VITE_LOCAL_MAILBOX_URL
RUN npm run build
FROM nginx:1.29-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist /usr/share/nginx/html
EXPOSE 8080
