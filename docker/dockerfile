# Use latest Arch Linux base image
FROM archlinux:latest

LABEL maintainer="feelfeel200088@gmail.com"

WORKDIR /app


RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm python python-pip nodejs npm curl git base-devel && \
    pacman -Scc --noconfirm


COPY . /app/Just_Another_Kahoot_Bot


RUN pip install --no-cache-dir --break-system-packages -r Just_Another_Kahoot_Bot/requirements.txt

RUN npm install --prefix /app/Just_Another_Kahoot_Bot

# Expose port
EXPOSE 8000


ENV PYTHONPATH="/app/Just_Another_Kahoot_Bot"


CMD ["python", "-m", "Just_Another_Kahoot_Bot"]




