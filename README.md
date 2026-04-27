# Automatizacion de emails con Gmail

Este proyecto lee destinatarios desde `recipients.csv`, toma el asunto y los cuerpos desde `messages.csv` y envia los correos con Gmail API usando OAuth y `credentials.json`.

## Archivos

- `recipients.csv`: lista de personas a las que quieres escribir.
- `messages.csv`: asuntos y archivos de cuerpo para cada `template_id`.
- `templates/`: textos del correo en `.txt` y opcionalmente `.html`.
- `attachments/`: carpeta sugerida para adjuntos.
- `credentials.json`: credencial OAuth descargada desde Google Cloud. No se sube a Git.
- `token.json`: token local creado al conectar Gmail. No se sube a Git.
- `.env.example`: ejemplo de configuracion opcional.
- `send_emails.py`: script de envio.
- `mail_mcp/`: aplicacion Flask modular con rutas, servicios, repositorios y assets web.

## Configurar Gmail

1. Habilita Gmail API en tu proyecto de Google Cloud.
2. Crea una credencial OAuth de tipo Desktop app.
3. Descarga el JSON y guardalo como `credentials.json` en la raiz del proyecto.
4. Instala dependencias:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

5. Conecta Gmail:

```bash
.venv/bin/python send_emails.py --auth
```

Ese comando abre el flujo de Google, pide permiso para enviar emails y guarda `token.json` para futuros envios.

Opcionalmente copia `.env.example` como `.env` para personalizar el nombre visible del remitente y `Reply-To`:


```bash
cp .env.example .env
```

## Probar antes de enviar

```bash
.venv/bin/python send_emails.py
```

Ese comando solo valida y muestra los correos preparados. No envia nada.

## Enviar

```bash
.venv/bin/python send_emails.py --send
```

## Interfaz web local

Crea un entorno virtual e instala dependencias:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Ejecuta la app:

```bash
.venv/bin/python web_app.py
```

Abre `http://127.0.0.1:5000`.

Desde la interfaz puedes editar templates, crear o borrar `template_id`, previsualizar HTML con datos de un recipient, administrar `recipients.csv`, ejecutar dry-run y enviar recipients seleccionados con confirmacion.

Tambien puedes conectar Gmail desde el boton `Conectar Gmail`. El envio real requiere que exista `token.json`; si no existe, conecta Gmail primero.

Antes de guardar cambios desde la web, la app crea una copia en `backups/YYYYMMDD-HHMMSS/`.

La interfaz web esta separada en `mail_mcp/web/templates/index.html`, `mail_mcp/web/static/css/app.css` y modulos JavaScript en `mail_mcp/web/static/js/`. El backend expone los mismos endpoints `/api/...`, pero la logica vive en servicios y repositorios testeables.

## Verificar

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python send_emails.py
```

## Personalizar datos

En `recipients.csv`, cualquier columna adicional puede usarse como variable dentro de los templates. Por ejemplo, `{first_name}`, `{company}` o `{custom_note}`.

Si quieres varios adjuntos para una persona, separalos con punto y coma en `attachment_paths`:

```csv
attachments/archivo1.pdf;attachments/archivo2.pdf
```

El script solo envia filas donde `send` sea `yes`, `si`, `sí`, `true`, `1` o `y`.
