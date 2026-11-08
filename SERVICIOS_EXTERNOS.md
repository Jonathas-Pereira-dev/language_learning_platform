# Servicios externos · configuración

## Recordatorios de entrega

La plataforma intenta enviar un aviso unas 24 horas y otro unas 2 horas antes del plazo. Solo se programan si el estudiante tiene acceso al contenido, no ha enviado la actividad y ha elegido un canal con consentimiento en **Actividades para entregar → Mis recordatorios de entrega**.

El servidor debe permanecer encendido. La revisión de plazos se ejecuta cada minuto. Los avisos pendientes se cancelan si se entrega la actividad, vence el plazo, cambia el docente o se desactiva el canal. Se evitan duplicados mediante registros persistentes. Los fallos de envío tienen hasta cuatro intentos con un intervalo de 15 minutos.

**Aceptado por el proveedor** no significa que se haya confirmado la lectura o recepción en el teléfono. Un envío interrumpido mientras estaba en proceso no se reenvía automáticamente para evitar duplicados; comprueba el proveedor.

### Correo electrónico

Configura en el mismo PowerShell donde ejecutarás el servidor:

```powershell
$env:SMTP_HOST = 'smtp.tu-proveedor.com'
$env:SMTP_PORT = '587'
$env:SMTP_FROM = 'clases@tu-dominio.com'
$env:SMTP_USER = 'tu-usuario'
$env:SMTP_PASSWORD = 'tu-contraseña-smtp'
```

Se utiliza STARTTLS. No se envían correos de prueba automáticamente. Sin configuración, el aviso figura como **Servicio sin configurar**.

### WhatsApp mediante Twilio

Se utiliza la [API oficial de plantillas de Twilio](https://www.twilio.com/docs/content/send-templates-created-with-the-content-template-builder). Necesitas una cuenta, un remitente habilitado para WhatsApp y una plantilla aprobada. El servicio puede tener costes.

Prepara una plantilla en español con tres variables, por ejemplo:

```text
Hola {{1}}. Recuerda entregar la actividad {{2}} antes de {{3}}.
Consulta la plataforma para enviar tu respuesta.
```

Variables: 1 = nombre del estudiante, 2 = actividad, 3 = plazo en UTC. Después configura:

```powershell
$env:TWILIO_ACCOUNT_SID = 'AC...'
$env:TWILIO_AUTH_TOKEN = 'tu-token'
$env:TWILIO_WHATSAPP_FROM = 'whatsapp:+numero-habilitado'
$env:TWILIO_CONTENT_SID = 'HX...'
```

Los valores son marcadores: reemplázalos por datos reales. El estudiante introduce su teléfono con prefijo internacional, como `+5511999999999`, y activa el canal voluntariamente. En el entorno de pruebas de Twilio, el destinatario debe estar habilitado en su sandbox.

La instalación en `127.0.0.1` solo se abre desde el propio equipo. Para estudiantes remotos y avisos continuos, necesitas una instalación compartida con el servidor en funcionamiento.

## Diccionario

El glosario didáctico local permite navegar por letras sin internet. Las demás consultas utilizan la [API de Wikcionario](https://www.mediawiki.org/wiki/API:Parsing_wikitext) y guardan las entradas encontradas para futuras consultas. Se muestran definiciones de la sección en español, fuente y atribución de licencia. No requiere clave.

El glosario local es limitado y editorial; no se presenta como un diccionario académico completo. Si la consulta externa falla o no hay entrada en español, se informa sin inventar definiciones.

## Vídeos disponibles y todos los países

El servidor comprueba periódicamente los enlaces admitidos. Los estudiantes solo reciben recursos marcados como disponibles; los recursos pendientes o no disponibles siguen visibles para que el docente los gestione. Una página accesible no garantiza reproducción desde cualquier país, ni elimina restricciones del editor.

Para buscar vídeos de los 21 países y regiones, configura una clave de la [YouTube Data API](https://developers.google.com/youtube/data/reference/rest/v3/search/list):

```powershell
$env:YOUTUBE_API_KEY = 'tu-clave'
```

En **Vídeos y curiosidades**, el docente abre **Buscar vídeos disponibles de cualquier país**, elige país y tema, revisa los resultados y pulsa **Preparar publicación**. Debe confirmar el nivel y la actividad antes de publicar.

La búsqueda comprueba que YouTube indique privacidad pública, procesamiento completo, inserción permitida y ausencia de restricciones regionales declaradas. No se inventan resultados si no hay coincidencias. La API tiene cuotas; consulta tu proyecto en Google Cloud.

Sin clave, la biblioteca inicial y los enlaces publicados por el docente siguen funcionando, pero **no se garantiza que haya vídeos para todos los países**. Las fuentes de verificación admitidas están definidas en `video_library.py`; no se consultan direcciones arbitrarias de red interna.

## Iniciar después de configurar

```powershell
cd C:\Fluentia
.\.venv\Scripts\python.exe app.py
```

Las variables definidas así duran lo que dure ese terminal. No guardes claves reales ni contraseñas en archivos del repositorio.
