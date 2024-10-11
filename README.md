# Udecbot Backend

Este es el backend del proyecto **Udecbot**, un chatbot desarrollado con **FastAPI**, **Python 3.10.11** y **PostgreSQL** que gestiona la inscripción, cancelación y listado de materias para estudiantes de una universidad. El proyecto está diseñado para que los estudiantes puedan interactuar con un chatbot que les permita inscribirse y gestionar sus materias de forma automatizada.

## Funcionalidades

- Inscripción de materias por parte del estudiante.
- Cancelación de materias.
- Listado de materias inscritas.
- Verificación de créditos disponibles (máximo 18 créditos por semestre).
- Inscripción automática de materias sin créditos (DN CAI).
- Validación de prerrequisitos y materias adelantadas.

## Requisitos previos

Asegúrate de tener instalados los siguientes programas antes de comenzar:

- Python 3.10.11
- PostgreSQL
- Git (opcional, para clonar el repositorio)

## Configuración del entorno

1. Clona este repositorio en tu máquina local:

   ```bash
   git clone https://github.com/tu_usuario/udecbot_backend.git
