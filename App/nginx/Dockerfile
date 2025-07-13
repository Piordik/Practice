FROM nginx:alpine

COPY conf.d/ /etc/nginx/conf.d/
RUN rm /etc/nginx/conf.d/default.conf
RUN mkdir -p /var/www/static