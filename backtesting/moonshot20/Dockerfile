ARG FF03_BASE
FROM ${FF03_BASE}
ARG SOURCE_SHA
USER root
COPY adapter.py /opt/moonshot20/adapter.py
RUN printf '#!/bin/sh\nexec python3 /opt/moonshot20/adapter.py "$@"\n' > /usr/local/bin/forecast && chmod 755 /usr/local/bin/forecast
LABEL org.opencontainers.image.revision=${SOURCE_SHA}
LABEL moonshot20.base.image_id="sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c"
LABEL moonshot20.performance="UNVERIFIED_HIGH_RISK"
USER 1000
WORKDIR /work
CMD ["forecast", "--help"]
