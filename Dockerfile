FROM python:3
WORKDIR /workspace
COPY . .
RUN pip install -r requirements.txt

ENV DISCORD_TOKEN a
ENV FACEIT_TOKEN b

CMD ["python", "./main.py"]
