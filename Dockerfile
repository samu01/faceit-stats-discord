FROM python:3.9
WORKDIR /workspace
COPY . .
RUN pip config --user set global.progress_bar off
RUN pip install -r requirements.txt

ENV DISCORD_TOKEN a
ENV FACEIT_TOKEN b
ENV STEAM_API_KEY c

CMD ["python", "./main.py"]
