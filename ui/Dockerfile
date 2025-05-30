FROM python:3.10-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Remove this line for development
COPY ./login_page.py /app/login_page.py 

# Dont know if this should be added??
# COPY ./.streamlit ./.streamlit

# Expose the port Streamlit will run on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "login_page.py", "--server.port=8501", "--server.address=0.0.0.0"]