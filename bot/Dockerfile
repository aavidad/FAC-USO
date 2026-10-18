FROM python:3.12-slim
WORKDIR /bot
COPY bot.py sources.json adapters_west.py adapters_huelva.py ./
USER 65534:65534
ENTRYPOINT ["python", "/bot/bot.py"]
