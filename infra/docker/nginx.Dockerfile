FROM nginx:1.27-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY infra/nginx/neyla.conf /etc/nginx/conf.d/neyla.conf

EXPOSE 80
