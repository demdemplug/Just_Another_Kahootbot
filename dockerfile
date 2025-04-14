# Use latest Arch Linux base image
FROM archlinux:latest

LABEL maintainer="feelfeel200088@gmail.com"

WORKDIR /app

# Install system dependencies including Rust
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
    python \
    python-pip \
    nodejs \
    npm \
    curl \
    git \
    rust \
    base-devel && \
    pacman -Scc --noconfirm

# Copy your app
COPY . /app/Just_Another_Kahoot_Bot

# Install Python dependencies (orjson will now work since Rust is installed)
RUN pip install --no-cache-dir --break-system-packages -r Just_Another_Kahoot_Bot/requirements.txt


# Expose the application port
EXPOSE 8000

# Set Python path to your app
ENV PYTHONPATH="/app/Just_Another_Kahoot_Bot"

# Run the app
CMD ["python", "-m", "Just_Another_Kahoot_Bot"]
