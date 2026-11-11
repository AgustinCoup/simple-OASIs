# simple-OASIs

## Ejecutar en Linux

Desde la raíz del proyecto:

```bash
python3 -m unittest discover -s tests -v
./docs/casos/correr_casos.sh
```

El script de casos necesita `OPENROUTER_API_KEY`. También se puede elegir el
modelo mediante `OASIS_MODEL`. Si ya existe la salida de un caso en
`docs/casos/salidas/`, el script la conserva y salta ese caso.

En Windows se puede usar `docs/casos/correr_casos.ps1`.