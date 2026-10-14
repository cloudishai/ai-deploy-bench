# Serves the site that `python -m website.build` writes to dist/. Cloudish builds this image from the
# context `python -m website.deploy` uploads: this file, nginx.conf and dist/.
# nginx's stable line, pinned by digest; it runs as an unprivileged user and listens on 8080.
FROM nginxinc/nginx-unprivileged:1.30-alpine@sha256:56b8272e43a0525f67aed68d1e0794a712d10e3e45a563e118e9a77c817e6f86
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html/
EXPOSE 8080
