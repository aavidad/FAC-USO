# Seguridad y operación

Los bots usan cuentas provinciales separadas con contraseñas de aplicación. El complemento valida el ámbito de escritura y la fuente; no deben recibir una cuenta administradora. El despliegue público requiere HTTPS y credenciales nuevas.

Las instrucciones de aprovisionamiento, permisos, cron, registros y retirada de la tarea están en [BOT_NOTICIAS.md](docs/BOT_NOTICIAS.md). La revisión focal y los ensayos locales figuran en [REVISION_INDEPENDIENTE.md](docs/REVISION_INDEPENDIENTE.md) y [PRUEBAS.md](docs/PRUEBAS.md). Esos ensayos no acreditan la configuración de un alojamiento futuro.

Los secretos, sesiones de navegador, archivos `.env`, `.runtime/` y el ODT original no se versionan ni se distribuyen en el paquete público. Antes de publicar un cambio se comprueban también los archivos ZIP, incluidos los paquetes anidados.

En las incidencias públicas describe el problema con datos inventados. Comunica por un canal privado del responsable cualquier credencial o información personal afectada. Si se expone una credencial, revócala y sustituye su archivo privado; borrar el texto de una revisión posterior no invalida la clave expuesta.
