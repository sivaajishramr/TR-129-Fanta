FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

ENV PORT=7860
ENV FLASK_ENV=production

CMD ["gunicorn", "--chdir", "backend", "app:app", "--bind", "0.0.0.0:7860", "--workers", "2"]
