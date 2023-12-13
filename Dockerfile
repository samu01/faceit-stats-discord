FROM python:3.9
WORKDIR /workspace
COPY . .
RUN pip config --user set global.progress_bar off
RUN pip install -r requirements.txt

ENV DISCORD_TOKEN a
ENV FACEIT_TOKEN b

CMD ["python", "./main.py"]
