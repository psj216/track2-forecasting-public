# ## Executive summary (read this first)
# Inherit the immutable verified V5.1 image and its complete pinned dependencies.
FROM docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874
USER root
COPY moonshot15_engine /opt/moonshot15_engine
RUN chmod 0555 /opt/moonshot15_engine/forecast && ln -s /opt/moonshot15_engine/forecast /usr/local/bin/m15-forecast
ARG M15_VARIANT
ARG SOURCE_SHA
ENV M15_VARIANT=${M15_VARIANT}
LABEL org.opencontainers.image.revision=${SOURCE_SHA}
LABEL agenthon.m15.variant=${M15_VARIANT}
LABEL agenthon.v51.source=47194f28d5188b87cdca1d591d86b9eeda86f7cf
USER runner
# Harness passes forecast as the first argument; a dedicated entrypoint strips only that verb.
ENTRYPOINT ["python3", "-m", "moonshot15_engine.entrypoint"]
CMD ["forecast", "--help"]
