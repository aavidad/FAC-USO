# Ensayo de los archivos de importación

Los dos archivos de `dist/` se prueban en un WordPress oficial 7.1.3 con PHP 8.3 dentro de Docker. La validación usa el MariaDB local existente, pero crea solo tablas con prefijos `facuso_ziptest_` y `facuso_wxrtest_`. El WordPress principal conserva sus tablas `wp_` y su volumen. El proxy de validación escucha únicamente en `127.0.0.1:18087`; el contenedor de WordPress solo pertenece a la red interna `facuso-importacion_local`. La configuración PHP compartida permite subir archivos de hasta 16 MB; `facuso-arranque.zip` ocupa unos 5,3 MB.

```bash
docker compose -f docker/compose.validation.yaml up -d
docker compose -f docker/compose.validation.yaml exec -T zip-wp php /pruebas/scripts/test_imports.php zip
docker compose -f docker/compose.validation.yaml exec -T zip-wp php /pruebas/scripts/test_imports.php subdir
docker compose -f docker/compose.validation.yaml exec -T -e WORDPRESS_TABLE_PREFIX=facuso_wxrtest_ zip-wp php /pruebas/scripts/test_imports.php xml
curl -fsSI http://127.0.0.1:18087/
```

Para repetir ambos ensayos desde una instalación vacía de sus **prefijos de validación**, ejecutar antes:

```bash
docker compose -f docker/compose.validation.yaml exec -T zip-wp php /pruebas/scripts/test_imports.php reset-zip
docker compose -f docker/compose.validation.yaml exec -T -e WORDPRESS_TABLE_PREFIX=facuso_wxrtest_ zip-wp php /pruebas/scripts/test_imports.php reset-xml
```

Los modos `reset-*` comprueban el prefijo exacto y borran únicamente tablas que comienzan con él. No se debe añadir `-v` a `docker compose down` si se desea conservar el núcleo descargado de WordPress para otro ensayo. Los secretos permanecen en `docker/.secrets/` y no se imprimen.

El modo `zip` extrae `facuso-arranque.zip` con `unzip_file`, activa el complemento e importa contenido y diseño. Comprueba los conteos del manifiesto JSON, nombres y jerarquía de páginas, noticias, categorías, menús, portada, tema, medios de la biblioteca y repetición sin duplicados. El modo `subdir` cambia temporalmente las opciones `home` y `siteurl` a `/portal`, comprueba que WordPress genere la ruta con ese prefijo y restaura ambas opciones. Además, se comprueba por HTTP que la portada y una página interior respondan con 200.

El modo `xml` usa [WordPress Importer 0.9.1](https://wordpress.org/plugins/wordpress-importer/) descargado de `https://downloads.wordpress.org/plugin/wordpress-importer.0.9.1.zip`; el ZIP local de la dependencia tiene SHA-256 `2101ebc2f685dd03a5ad715c96b8580d663625df5e4780711d18f0c48a2f9194`. Comprueba páginas, noticias, categorías, menús y ausencia de marcas de imágenes dependientes del complemento. El XML es una alternativa de contenido: WordPress Importer no importa por sí solo el tema, los medios ni configura la portada. Las imágenes que apuntan al directorio del tema requieren instalar también `facuso-andalucia-tema.zip`. Para una web completa se utiliza `facuso-arranque.zip`.

La ejecución del importador se hace con `WP_HTTP_BLOCK_EXTERNAL` y sin descarga de adjuntos remotos. La revisión de seguridad se ha centrado en la separación de prefijos, el enlace del proxy a loopback, el aislamiento de red, la gestión de secretos y la instalación desde los paquetes locales. No se envió código ni datos a un servicio de auditoría externo.

## Resultado del paquete de 18/10/2026

| Ensayo | Resultado |
| --- | --- |
| ZIP en WordPress limpio | 598 comprobaciones, 0 errores; 74 páginas, 132 noticias, 39 categorías, 2 menús y 34 imágenes en la biblioteca. |
| ZIP repetido | 0 contenidos nuevos, 0 conflictos y ningún medio duplicado. |
| XML con WordPress Importer oficial 0.9.1 | 557 comprobaciones, 0 errores; 74 páginas, 132 noticias, 39 categorías y 2 menús. |
| Enlaces con `/portal` | 552 comprobaciones, 0 errores. |
| Portada, «Conócenos», ocho páginas de empleo público y tres de OPAEF | Las 13 rutas respondieron HTTP 200 desde `127.0.0.1:18087`. |

Los resultados íntegros, los prefijos usados, las trece rutas HTTP y los hashes están en [importaciones-final.json](evidencias/importaciones-final.json). Las salidas individuales se conservan en `docs/evidencias/importacion-{zip,subdir,xml}.json`.

SHA-256 de los archivos ensayados: `facuso-arranque.zip` = `7f33e55a20dcbb8302060e051d44b972cb43c4b0eeef0d7cc0116001e167c06d`; `facuso-andalucia.xml` = `1d7648048197ed6446f8ea14a45d394395b82e111076df0e251b3acdca808805`; `facuso-andalucia-tema.zip` = `bbe3d698b66416e03ff885bf135013ad04f7b8cf98cbe75af8895607d40444f7`.
