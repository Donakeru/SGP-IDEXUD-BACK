

FROM python:3.12.3-slim


# preguntar si se va a utilizar un entorno virtual dentro del docker
#
# ENV VIRTUAL_ENV=/venv
# RUN python -m venv "$VIRUTAL_ENV" 
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"


# directorio donde se almacenará el proyecto dentro del contenedor
WORKDIR /sgp-app

COPY requirements.txt .

# instalar dependencias
#
# RUN python -m pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]