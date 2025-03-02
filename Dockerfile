# Set working directory
WORKDIR /app

# Copy only the necessary files first (to optimize caching)
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy the "app" folder *contents* directly into /app, not the folder itself
COPY app/ ./

# Expose Flask's default port
EXPOSE 5001

# Run the application
CMD ["python", "/app/app.py"]
