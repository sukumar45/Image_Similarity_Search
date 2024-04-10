FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit_client.py .


EXPOSE 8501

CMD ["streamlit", "run", "streamlit_client.py"]
