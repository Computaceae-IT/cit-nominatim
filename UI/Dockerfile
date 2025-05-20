FROM python:3.9.4-buster

LABEL maintainer="SiropOps <cyril@botalista.community>"

# Nominatim install.
ENV NOMINATIM_UI_VERSION 3.0.5

RUN wget -O nominatim-ui.tar.gz https://github.com/osm-search/nominatim-ui/releases/download/v$NOMINATIM_UI_VERSION/nominatim-ui-$NOMINATIM_UI_VERSION.tar.gz  && \
	mkdir -p /app/nominatim  && \
    tar xzvf nominatim-ui.tar.gz -C /app/nominatim --strip-components 1


ADD config.defaults.js /app/nominatim/dist/theme/config.theme.js
ADD config.defaults.js /app/nominatim/dist/config.defaults.js

WORKDIR /app/nominatim/dist

EXPOSE 8765

CMD ["python3", "-m", "http.server", "8765"]
