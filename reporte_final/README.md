# Evidencia para el reporte final

Este directorio contiene la evidencia técnica utilizada para documentar
el sistema local multiagente basado en Qwopus3.6, OpenClaude e ik_llama.cpp.

## Contenido

### 01_final_benchmark

Evidencia directa de la última ejecución exitosa:

- server.log
- gpu.csv
- prompts de los agentes
- código inicial y final
- pytest
- git diff
- eventos internos del motor
- timings de inferencia

### 02_engine

Snapshot del motor de inferencia utilizado:

- código fuente completo de ik_llama.cpp en tar.gz
- archivos fuente más relevantes para inspección directa
- metadatos Git
- versión del servidor
- template Qwen3.6
- documentos de validación

### 03_configuration

Información necesaria para reproducir y documentar el experimento:

- comando final del servidor
- entorno de software/hardware
- resumen del resultado final

## Resultado final

Agent A: 8/8 PASS

Agent C: 8/8 PASS AFTER AUTONOMOUS RECOVERY

Total: 16/16 PASS
