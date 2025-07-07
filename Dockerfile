# Python 3.11 slim
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema para OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar Python packages
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO el código
COPY . .

# Mover app.py a la raíz si está en backend/
RUN if [ -f "backend/app.py" ]; then \
        echo "📁 Moviendo backend/app.py a la raíz"; \
        cp backend/app.py ./main_app.py; \
    elif [ -f "app.py" ]; then \
        echo "📁 app.py ya está en la raíz"; \
        cp app.py ./main_app.py; \
    else \
        echo "❌ ERROR: No se encontró app.py"; \
        find /app -name "app.py" -type f; \
        exit 1; \
    fi

# Exponer puerto
EXPOSE $PORT

# Ejecutar la app desde la raíz
CMD python main_app.py