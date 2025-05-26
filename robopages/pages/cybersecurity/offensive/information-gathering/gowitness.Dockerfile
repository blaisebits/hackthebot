FROM golang:1-bookworm AS build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Clone and build gowitness
RUN git clone https://github.com/sensepost/gowitness.git /src
WORKDIR /src

# Build frontend and backend
RUN cd web/ui && \
    npm install && \
    npm run build && \
    cd ../..

RUN go install github.com/swaggo/swag/cmd/swag@latest && \
    swag i --exclude ./web/ui --output web/docs && \
    CGO_ENABLED=0 go build -v -trimpath -ldflags="-s -w" -o gowitness

FROM debian:bookworm-slim

# Install Chromium and other dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    chromium \
    chromium-driver \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

# Copy built binary from build stage
COPY --from=build /src/gowitness /usr/local/bin/gowitness

# Set Chrome path for gowitness
ENV CHROME_PATH=/usr/bin/chromium

VOLUME ["/screenshots"]
WORKDIR /screenshots

ENTRYPOINT ["dumb-init", "--", "gowitness"]