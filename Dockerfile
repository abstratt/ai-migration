FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV SDKMAN_DIR=/home/claude/.sdkman
ENV PATH="${SDKMAN_DIR}/bin:${PATH}"

ENV GRADLE_OPTS="-Xmx4g"

# Non-root user for claude (refuses to run as root)
RUN useradd -m -u 1001 -s /bin/bash claude

# Base tools
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    unzip \
    zip \
    ca-certificates \
    gnupg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Claude Code
RUN npm install -g @anthropic-ai/claude-code

# GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-c"]

# Bake the migration plan into the image
COPY MIGRATION.md /MIGRATION.md

RUN chown -R claude:claude /home/claude

USER claude
WORKDIR /workspace

# SDKMAN (used by Claude to install the required JDK at runtime)
RUN curl -s "https://get.sdkman.io" | bash \
    && bash -c "source ${SDKMAN_DIR}/bin/sdkman-init.sh && sdk version"

# Pre-warm JDK 25 to speed up runs
# Claude will install others on demand via `sdk install java`
RUN bash -c " \
    source ${SDKMAN_DIR}/bin/sdkman-init.sh && \
    sdk install java 25.0.2-tem \
"

CMD ["/bin/bash"]



