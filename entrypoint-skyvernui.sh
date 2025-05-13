#!/bin/bash
set -e

# Compilar o frontend para produção
npm run build

# Servir o frontend compilado
npm run preview -- --host 0.0.0.0 --port 80
