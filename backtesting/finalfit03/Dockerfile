# Executive summary: standalone monthly adapter over the exact immutable safe runtime.
FROM jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874
ARG SOURCE_SHA
USER root
COPY candidate_monthly.py official_horizons.py /opt/finalfit03/
RUN printf '#!/bin/sh\nexec python3 /opt/finalfit03/candidate_monthly.py "$@"\n' > /usr/local/bin/forecast && chmod 755 /usr/local/bin/forecast
LABEL qfbench2.interface_version="2.0" qfbench2.track="forecasting" qfbench2.verb="forecast"
LABEL org.opencontainers.image.revision=${SOURCE_SHA}
LABEL org.opencontainers.image.base.digest="sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874"
USER 1000
WORKDIR /work
CMD ["forecast", "--help"]
