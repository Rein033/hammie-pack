# Crea tu propio avatar con Claude o ChatGPT

*[English](AVATAR.md) · Español*

Hammie es un avatar. Con **Kode Avatar** creas el tuyo: un gato, un robot, tú mismo en dibujo.
Un chat de IA (Claude o ChatGPT) dibuja cada animación como archivo Lottie. La app Kode Avatar
comprueba cada archivo con las reglas del propio kodeOS y los empaqueta en un face pack para el
Kode Dot.

**Abre la app: <https://rein033.github.io/kode-avatar/app/?lang=es>**

Todo funciona en tu navegador. No se sube nada. Tu trabajo se guarda en el navegador hasta que
pulses *Borrar todo*.

> [!WARNING]
> Los face packs **todavía no se han probado en un Kode Dot oficial**. La app hace las mismas
> comprobaciones que kodeOS (`kui_pack.c`), pero la vista previa la dibuja tu navegador, no el
> Dot. Prueba tu pack primero desde una tarjeta microSD: al sacar la tarjeta vuelve Kody.

## Qué necesitas

- Una cuenta gratuita en [Claude](https://claude.ai) o [ChatGPT](https://chatgpt.com).
- Un Kode Dot con un kodeOS que tenga face packs, y una tarjeta microSD (o Wi-Fi, ver abajo).

## Las doce animaciones

| Tarjeta en la app | Cuándo la reproduce el Dot | Lienzo | Obligatoria |
|---|---|---|---|
| Despertar | la cara aparece al encenderse la pantalla | 410 x 334 | sí |
| Reposo (bucle) | la cara, en bucle todo el día | 410 x 334 | sí |
| Te mira | alguien levanta o toca el Dot | 410 x 334 | |
| En punto | cada hora en punto | 410 x 334 | |
| Notificación | llega una notificación | 410 x 334 | |
| Cargando | se conecta el cable USB | 410 x 334 | |
| Broma 1, Broma 2 | de vez en cuando, al azar | 410 x 334 | |
| Sin apps | el lanzador sin apps | 410 x 369 | |
| Instalando | la tarjeta mientras se escribe una app | 410 x 160 | |
| Adiós | la tarjeta justo antes de que arranque una app | 410 x 160 | |
| Cargando app | la pantalla de carga | 264 x 264 | |

Solo **Despertar** y **Reposo** son obligatorias. Empieza con esas dos, ponlas en el Dot y añade
el resto después.

## Paso a paso

1. **Describe tu personaje** en la app. Nombra sus colores, su forma y un objeto. Por ejemplo:
   *"Un gato gris y redondo con grandes ojos verdes, nariz rosa, bigotes cortos y unos pequeños
   auriculares amarillos. Vista de frente, cabeza y parte superior del cuerpo, ocupando casi toda
   la pantalla."*
2. **Abre un chat nuevo** en Claude o ChatGPT. Usa un solo chat para todo el avatar, así la IA
   mantiene el mismo dibujo.
3. En la tarjeta **Reposo**, pulsa **Copiar prompt** y pégalo en el chat. El prompt ya contiene
   todas las reglas del Dot (lienzo, velocidad, tamaño, qué funciones de Lottie evitar).
4. Copia la respuesta completa de la IA. En la tarjeta Reposo, pulsa **Pegar respuesta**, pega y
   pulsa **Usar esto**. La app encuentra el JSON en la respuesta, lo reproduce y lo comprueba.
   - **✓ Válido para el Dot**: sigue.
   - **✗ El Dot rechazaría esto**: la lista dice por qué. Pega esa línea en el chat: *"El
     comprobador dice: … Arréglalo y envía de nuevo el JSON completo."*
   - Las líneas amarillas son avisos: cosas que el Dot quizá no dibuje (imágenes, texto, efectos).
5. Haz lo mismo con **Despertar** y luego con las demás tarjetas. ¿Ya te gusta Reposo? **Igual que
   Reposo** o **Reposo, escalado** llena una tarjeta con tu animación de reposo, escalada al
   lienzo de esa tarjeta.
6. Pulsa **Descargar face pack (.zip)**.

### Consejos para buenos resultados

- **Claude** con *Artifacts* puede mostrar la animación mientras trabaja. Pídele: *"Muéstralo
  también como vista previa Lottie."* ChatGPT puede hacer lo mismo con su herramienta de código.
- ¿Se cortó la respuesta, o la app dice *"No se pudo leer el JSON"*? Pide *"Hazlo más corto: menos
  formas y fotogramas clave, y envía de nuevo el JSON completo."* El Dot permite 96 KB por
  animación.
- ¿Tamaño incorrecto? Pulsa **Ajustar al lienzo**. Escala la animación al lienzo correcto,
  centrada.
- Hazlo sencillo. Formas grandes y planas, pocos colores, de 2 a 4 segundos por animación. La
  pantalla del Dot es pequeña y las formas simples se dibujan más rápido.
- ¿Ya tienes un Lottie de [LottieFiles](https://lottiefiles.com) o de After Effects (Bodymovin)?
  Usa **Subir .json**. Revisa antes su licencia.
- ¿Prefieres modificar a Hammie? Pulsa **Empezar con Hammie** y reemplaza las tarjetas que quieras.

## Ponerlo en el Dot

### Con una tarjeta microSD (lo más fácil)

1. Formatea la tarjeta en FAT32.
2. Descomprime la descarga. Contiene una carpeta `kode`.
3. Copia esa carpeta `kode` a la raíz de la tarjeta, para que tenga `/kode/kode.json`.
4. Pon la tarjeta en el Dot y reinícialo.

**Volver a Kody:** saca la tarjeta, o borra la carpeta `kode`, y reinicia.

### Por Wi-Fi

1. Sube los archivos de la carpeta `kode` a internet, por ejemplo a un repositorio público de
   GitHub tuyo.
2. Abre la consola del Dot por USB-C (cualquier terminal serie, ver el [README](../README.md#b-over-wi-fi-from-this-repository)).
3. Escribe, con el enlace a **tu** `kode.json`:

   ```
   function name="assets_update" arg="https://raw.githubusercontent.com/TU/REPO/main/kode.json"
   ```

**Volver a Kody:** `function name="assets_update"` sin `arg`.

## Comparte tu avatar

¿Te ha quedado bien? Ponlo en un repositorio público con los archivos de `kode` y un GIF, y abre
un issue en [kode-avatar](https://github.com/Rein033/kode-avatar/issues) con el enlace. No
compartas avatares de personas reales sin su permiso, ni de personajes que no sean tuyos.

## Para desarrolladores

La app son tres archivos, sin paso de compilación: [`app/index.html`](../app/index.html),
[`app/pack.js`](../app/pack.js) y [`app/i18n.js`](../app/i18n.js) (textos en inglés y español).
`pack.js` contiene las comprobaciones (los límites de `kui_pack.h` de kodeOS), la misma reducción
de JSON que `src/dotpack.py`, zlib, SHA-256, el manifiesto y un escritor de ZIP. Su resultado pasa
[`tools/packcheck`](../tools/packcheck).
