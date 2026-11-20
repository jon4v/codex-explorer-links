# Codex Explorer Links

A small Python CLI for Windows and WSL. Generate a clickable link to reveal a file in Windows Explorer from Codex or a terminal. Works locally with the Python standard library. Independent community project.

Comparte un vínculo clicable a un archivo de tu propio equipo. Desde la terminal, un clic en el vínculo abre el Explorador de Windows con el archivo seleccionado. Si el navegador trata el vínculo como una vista previa, aparece el botón **Mostrar en el Explorador de Windows**. El archivo puede ser un 3MF, una imagen, un HTML o cualquier otro archivo existente.

## Instalación

Con Python 3.9 o posterior y [pipx](https://pipx.pypa.io/stable/installation/), ejecuta esto en PowerShell o WSL:

```console
pipx install https://github.com/jon4v/codex-explorer-links/releases/download/v1.0.0/codex_explorer_links-1.0.0-py3-none-any.whl
```

Si el comando instalado aún no aparece en tu terminal, ejecuta `pipx ensurepath` y abre una terminal nueva. Para quitar la herramienta, usa `pipx uninstall codex-explorer-links`.

## Primer enlace

Desde la carpeta donde guardaste el archivo, en PowerShell o WSL:

```console
codex-explorer-links "modelo.3mf"
```

También puedes pasar varios archivos y elegir cuánto duran los enlaces:

```console
codex-explorer-links --hours 2 "modelo.3mf" "visor.html"
```

Si prefieres leer y ejecutar el código directamente, descarga el código fuente desde [GitHub Releases](https://github.com/jon4v/codex-explorer-links/releases). Desde la carpeta extraída usa `py -3 explorer_links.py "modelo.3mf"` en Windows o `python3 explorer_links.py "modelo.3mf"` en WSL.

Cada línea de salida contiene el nombre y un vínculo. Pega el vínculo en Codex o usa Markdown con la etiqueta «Mostrar el modelo en el Explorador». Para una entrega con varios archivos, pásalos todos en la misma invocación. Los enlaces normales de Codex siguen disponibles para previsualizar. El navegador puede dejar abierta una pestaña de confirmación.

El proceso atiende únicamente en el bucle local IPv4. Requiere que el navegador y el Explorador estén en el mismo equipo. En WSL, el navegador de Windows necesita acceso al puerto local de WSL. El servicio dura 24 horas por defecto, hasta 168 con `--hours`; Ctrl+C lo termina antes. Al cerrar el proceso, reiniciar el PC o mover el archivo, crea vínculos nuevos. Para compartir la herramienta, envía la página del proyecto. Cada persona genera enlaces en su propio equipo.

## Cómo usarlo desde un agente

Para entregar archivos en Windows, ejecuta el comando una vez con las rutas finales. Mantén vivo ese proceso durante el periodo indicado y usa las URLs que imprimió para los enlaces «Mostrar en el Explorador». Indica su vigencia y conserva también las rutas de los entregables para uso posterior. No inventes ni reutilices URLs de procesos vencidos.

## Qué se expone

Cada enlace lleva un identificador aleatorio, asociado en memoria con un único archivo elegido al arrancar. El servicio no enumera carpetas ni transmite los archivos. Las lecturas de previsualización muestran un botón; el envío de ese formulario requiere el mismo origen. Una navegación directa desde una aplicación puede solicitar la selección de inmediato. Quien tenga el enlace y acceso al mismo equipo puede pedir esa selección. No se necesita administrador, registro de protocolos ni servicios de inicio.

## Prueba

Ejecuta `python3 -m unittest -v` en WSL o `py -3 -m unittest -v` en Windows. Las pruebas usan dos archivos temporales y un Explorador simulado. Para comprobar la integración real, abre el vínculo de un archivo y verifica que el Explorador lo haya seleccionado.

## Licencia

[MIT](LICENSE).
