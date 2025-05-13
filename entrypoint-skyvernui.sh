#!/bin/bash
set -e

# Para desenvolvimento
# npm run dev

# Para produção
npm run build
npm run preview -- --host 0.0.0.0 --port 80
