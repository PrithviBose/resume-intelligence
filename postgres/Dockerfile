FROM postgres:17

RUN apt-get update && \
    apt-get install -y figlet && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/custom-entrypoint.sh

RUN chmod +x /usr/local/bin/custom-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/custom-entrypoint.sh"]

CMD ["postgres"]
