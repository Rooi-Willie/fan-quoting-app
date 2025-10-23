FROM python:3.10-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ./Login_Page.py /app/Login_Page.py
COPY ./pages /app/pages
COPY ./templates /app/templates
COPY ./images /app/images
COPY ./*.py /app/

# Copy Streamlit configuration
COPY ./.streamlit /app/.streamlit

# Switch to production configuration
RUN python switch_config.py prod

# Expose the port Streamlit will run on
EXPOSE 8501

# Set environment to production
ENV ENVIRONMENT=production

# Command to run the application
CMD ["streamlit", "run", "Login_Page.py", "--server.port=8501", "--server.address=0.0.0.0"]