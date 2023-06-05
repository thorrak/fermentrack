FROM nginx:1.18.0-alpine

COPY ./compose/production/nginx/nginx.conf /etc/nginx/nginx.conf
#COPY ./compose/production/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Uncomment the following 2 lines and change the .crt and .key names to the ones you have created
#COPY ./compose/production/nginx/MY_SELF_SIGNED_CERT.crt /etc/nginx/MY_SELF_SIGNED_CERT.crt
#COPY ./compose/production/nginx/MY_SELF_SIGNED_KEY.key /etc/nginx/MY_SELF_SIGNED_KEY.key
