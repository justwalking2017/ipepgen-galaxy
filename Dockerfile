FROM python:3.12-slim

LABEL org.opencontainers.image.title="iPepGen Galaxy CLI"
LABEL org.opencontainers.image.source="https://github.com/justwalking2017/ipepgen-galaxy"

WORKDIR /opt/ipepgen
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY workflows ./workflows
RUN pip install --no-cache-dir .

ENTRYPOINT ["ipepgen"]
CMD ["--help"]
