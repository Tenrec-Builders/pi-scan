# Resumen de Pi Scan

Pi Scan es un controlador de cámaras de fotos robusto y simple, diseñado especialmente para los escáneres de libros. Fue creado para trabajar con el escáner de libros Archivista(http://diybookscanner.org/archivist). Para preguntas o ayuda, visite el foro(http://diybookscanner.org/forum) o envíe un correo solicitando ayuda a help [at] tenrec [punto] builders.

# Requerimientos

* Raspberry Pi 2 o Raspberry Pi 3
* Dos cámaras(Canon PowerShot A2500 o Canon PowerShot ELPH 160 (también conocida como IXUS 160))
* Tres tarjetas SD de 4GB (2 para las cámaras, 1 para la Raspberry Pi). Es necesario que una de las tarjetas sea micro SD (para la Raspberry Pi). Las otras dos pueden ser de tamaño estándar, o tener adaptadores en caso de que sean micro.
* Un dispositivo de almacenamiento USB (puede ser un lector de tarjetas SD y una tarjeta SD veloz, o un pendrive)
* Dispositivos de entrada (ver más abajo)

# Opciones de dispositivos de entrada

En la medida de lo posible, hay que evitar utilizar un hub USB. Un porcentaje significativo de errores que los usuarios reportaron, eran causados por algún problema con el hub USB que se resolvieron enchufando los dispositivos directamente a la Raspberry Pi.

Un error conocido es que los dispositivos USB sólo funcionan si están enchufados a la Raspberry Pi previamente al encendido de la Pi. Si se enchufan luego del encendido o si se desenchufan, entonces será necesario reiniciar Pi Scan para que funcionen.

## Mouse

El Pi Scan puede ser controlado enteramente a través de un mouse y una pantalla con entrada HDMI (o en su defecto, con un adaptador HDMI-VGA). Este tipo de opción es incompatible con la opción táctil, pero funciona con todo otro tipo de dispositivos de ingreso de datos. Si la intención es utilizar el Pi Scan con un mouse, hay que descargarse la imagen de Pi Scan compatible con mouse que se encuentra más abajo.

## Pantalla táctil

Pi Scan trabaja con la pantalla táctil oficial de Raspberry Pi. Esto provee un escáner de libros más compacto y autónomo. La opción táctil es incompatible con el mouse. Si se desea utiliza la pantalla táctil, hay que descargarse la imagen de Pi Scan compatible con la pantalla táctil.

## Teclado

Pi Scan ahora puede ser controlado enteramente a través de un teclado. Cada botón de la pantalla muestra la tecla a la que responde, generalmente un número. El teclado funciona tanto con la versión táctil como la versión mouse de Pi Scan. Para navegar a través de las vistas con un teclado, hay que utilizar las teclas '+', '-', y '0' para configurar el nivel de zoom y mover la ventana con la combinación WASD o con las teclas de flecha. Cuando se digitaliza, para hacer la captura se pueden utilizar la barra espaciadora o las letras 'b' o 'c'.

## Pedal USB

La mayoría de los pedales USB de pie emulan un teclado y envían la tecla 'b' por defecto. Dado que la tecla 'b' es una combinación de tecla para captura, los pedales USB de pie pueden ser utilizados para disparar la captura de páginas.

## Pedal de pie industrial

Los pedales de pie industriales son más robustos que los pedales USB de pie equivalentes en precio. Pero no tienen la electrónica que se necesita para lidiar con los protocolos USB. Se pueden conectar hasta dos pines en la Raspberry Pi, y Pi Scan tratará cualquier conexión entre esos pines como un disparador para la captura durante la digitalización. Nótese que esto sólo capturará imágenes en la pantalla de digitalización, y no sirve para configurar foco, nivel de zoom, o tiempo de exposición. Para más detalles, véase el [manual de ensamblado] del Archivista Pluma (http://tenrec.builders/quill/guide/electronics/pedal/).

## Botones y microinterruptores

Cualquier conexión eléctrica entre el GPIO21 y los pines GND en la Raspberry Pi causará una captura (disparo) mientras se digitaliza. Por lo tanto, cualquier botón o microinterruptor puede servir como un gatillo de digitalización si está conectado correctamente.

# Actualizando el software de Pi Scan

A partir de la versión Pi Scan 0.8 o posteriores, es posible actualizar la instalación sin necesidad de descargar toda la imagen y re-grabándola sobre la tarjeta SD. Solo es necesario descargar el archivo de 'update' linkeado más abajo, copiarlo al dispositivo de almacenamiento externo (en la carpeta de root, no en las carpetas de 'images' o 'debug'), e iniciar el arranque de Pi Scan. Tocar 'Begin Scan'. Una vez que el dispositivo de almacenamiento externo cargó, debería verse un botón con la palabra 'Upgrade', en la parte superior derecha. Hay que tocar ese botón. La actualización debería tomar unos segundos. 

Si el proceso mencionado arriba no funciona, hay que descargar la imagen de más abajo y reinstalarla en la tarjeta.

* [Actualización a Pi Scan 1.0](http://tenrec.builders/pi-scan/1.0/pi-scan-update-1.0.archive)

# Descarga

Tanto la Raspberry Pi 2 como la Raspberry Pi 3 son compatibles con Pi Scan. Hay dos variantes. Una versión es compatible con el mouse y cualquier pantalla HDMI. La otra versión es compatible con la pantalla táctil oficial de Raspberry Pi:

* [Imagen de Raspberry Pi (para mouse)](http://tenrec.builders/pi-scan/latest/pi-scan-latest-mouse.zip)
* [Imagen de Raspberry Pi (para pantalla táctil)](http://tenrec.builders/pi-scan/latest/pi-scan-latest-touch.zip)

Dos modelos de cámaras son compatibles. Hay que descargarse la imagen compatible con cada cámara:

* [Imagen de Canon PowerShot A2500](http://tenrec.builders/pi-scan/latest/pi-scan-camera-a2500-latest.zip)
* [Imagen de Canon PowerShot ELPH/IXUS 160](http://tenrec.builders/pi-scan/latest/pi-scan-camera-elph160-latest.zip)

Estas imágenes se utilizan a propio riesgo del usuario. Estas imágenes pueden dañar la cámara. Durante el testeo previo de una imagen de la ELPH 160, una cámara fue dañado y la causa nunca fue encontrada definitivamente. Ver más en [este link](http://chdk.setepontos.com/index.php?topic=12321.140).

Otras cámaras compatibles con CHDK pueden o no funcionar. Si se desea probar la compatibilidad de estas cámaras, lo que hay que hacer es instalar la versión full del paquete de CHDK que corresponde a la cámara y al firmware que utiliza la cámara. Si funciona, ¡genial! Si no funciona, quizás sea necesario buscar en el log de debug, en el código y en los foros de CHDK para ver por qué no funciona. Mientras que no puedo hacer que otras cámaras sean compatibles, estoy dispuesto a aceptar requerimientos con parches para hacer que el Pi Scan sea compatible con otras cámaras.

# Instalación

El software está empacado como una imagen completa que necesita ser instalada en la tarjeta SD, que necesita tener al menos 4GB. Como no se almacena nada en estas tarjetas, no importa la velocidad de la tarjeta.

Para instalar la imagen en la tarjeta, es necesario extraer la imagen del archivo y utilizar una herramienta apropiada para instalarla en la tarjeta. No hay que copiar la imagen directamente en la tarjeta. Esto no va a funcionar. 

Si se está actualizando las tarjetas de las cámaras, puede ser que las cámaras estén en posición de "lock" o cerradas. Antes de instalar nada en las tarjetas, es necesario desbloquearlas. El pequeño interruptor a la izquierda tiene que estar en la posición superior, para desbloquear la tarjeta.

Tutoriales para escribir las imágenes en las tarjetas: [FALTAN LINKS EN CASTELLANO ACÁ]

* [Windows](https://www.raspberrypi.org/documentation/installation/installing-images/windows.md)
* [Mac](https://www.raspberrypi.org/documentation/installation/installing-images/mac.md)
* [Linux](https://www.raspberrypi.org/documentation/installation/installing-images/linux.md)

## Escribiendo una tarjeta SD en Windows

Vas a necesitar:

* El Win32 Disk Imager ([link](http://sourceforge.net/projects/win32diskimager/))
* Un lector de tarjetas SD
* Una tarjeta SD (hay que asegurarse que la tarjeta SD esté desbloqueada. El interruptor a la izquierda tiene que estar arriba de todo, en posición de desbloqueo).
* Una imagen de disco descargada de algunos de los links anteriores.
* Al menos 4GB libres de espacio en el disco.

La imagen que se descarga es un archivo ZIP comprimido. Hay que hacer click derecho y seleccionar del menú la opción "Extraer todo..." y elegir un directorio o carpeta de destino para los archivos extraídos.

Luego, inserte la tarjeta SD en el lector de tarjetas.

Ejecute el Win32 Disk Imager. Se le consultará si quiere permitirle que haga cambios, seleccione que sí.

Seleccione el directorio donde está montada la tarjeta SD en el menú de "dispositivo". Seleccione "Mi PC" o "Buscador de directorios" y verifique que ese es el dispositivo correcto.

Haga click sobre el botón "Escribir". Esto borrará todo lo que haya en la tarjeta y escribirá los contenidos de la imagen al directorio donde está montada la tarjeta SD. Por lo tanto, es importante asegurarse que la información esté siendo escrita efectivamente en la tarjeta y no en otro lugar.

## Utilizando las tarjetas SD

Una vez que las imágenes están instaladas, habrá tres tarjetas SD. Una necesita ser insertada en la Raspberry Pi 2. Las otras dos tarjetas con CHDK son para las cámaras. Las tarjetas de las cámaras ahora tienen que estar en la posición de "lock", bloqueadas. El pequeño interruptor en la izquierda tiene que estar en la posición inferior.

Cuando enciendas las cámaras, saltará una pantalla de CHDK que aparecerá brevemente. Así es cómo se sabe que el proceso de instalación tuvo éxito. Si no se ve esta pantalla en cada cámara, las tarjetas no están bloqueadas o hubo otro tipo de error durante la instalación.

A veces cuando se encienden las cámaras, una pantalla aparece solicitando que se le configure la hora y la fecha y la zona horaria. Esto ocurrirá la primera vez que las cámaras se enciendan, o si han estado desconectadas y sin utilizar por mucho tiempo. Si esto sucede, hay que desconectar el cable USB de la cámara, utilizar el botón de menú de la cámara para configurar la fecha y la hora, y luego reconectarla al USB.

A continuación, hay que enchufar las cámaras a la Raspberry. Insertar la tarjeta SD en la Raspberry. Conectar un monitor, un mouse y (opcional) un teclado a la Raspberry. Encender la Raspberry. Nótese que no hay ningún modo de red para este software. Funciona directamente al conectar dispositivos de entrada y salida en la Raspberry. 

# Utilización de Pi Scan

Para ver un resumen de cómo utilizar Pi Scan, ver el [video tutorial (en inglés)](https://vimeo.com/150385938).

El sistema operativo de Pi Scan es completamente de lectura. Todo lo producido se salva en una tarjeta SD externa a través de un lector de tarjetas SD, o en un dispositivo de almacenamiento externo. Los logs para hacer debug, la configuración y las imágenes digitalizadas, todo termina ahí. Cada vez que se regrese a la pantalla de inicio, Pi Scan desmontará el dispositivo externo para que se pueda remover de manera segura o bien apagar la Raspberry.

Hay muchas configuraciones de la cámara que todavía no pueden ser configuraradas por el usuario. Estas configuraciones están fijadas en valores que asumen que el usuario está utilizando un modelo de escáner como el Archivista. 

## Pasos para digitalizar

1. Encender la Raspberry Pi. Una vez que arranca, se verá la pantalla de inicio. Cuando estás en esta pantalla, Pi Scan ejecutará el disco externo para que se pueda remover. También se puede pasar al modo de consola (o de línea de comandos) utilizando el usuario 'pi' y la contraseña 'raspberry'. Para la mayoría de los usuarios, esto no será necesario.

1. En la página de configuración de los discos, Pi Scan busca y monta el almacenamiento externo. El almacenamiento externo es utilizado para los registros de configuración y de debugeo, y es donde se guardan las imágenes. El usuario debe enchufar el dispositivo USB o el lector de tarjetas de memoria con la tarjeta de memoria. Luego de unos segundos, el dispositivo será detectado y el usuario podrá apretar el botón de "siguiente" (next). Si el dispositivo no es detectado, hay que desconectarlo y volver a conectarlo a la Raspberry. 

1. En la página de configuración de la cámara, Pi Scan busca dos cámaras conectadas vía USB a la Raspberry. Una vez que las encuentra, se puede configurar el nivel de zoom, de manera opcional, o bien pasar al siguiente paso.

1. (Opcional). El zoom se puede configurar para cada cámara de manera individual. Para cada cámara, se debe apretar el botón de "disparo de prueba" para capturar una foto de cada cámara, y luego ajustar las configuraciones de zoom en las esquinas superiores de la izquierda y de la derecha. Por ahora, no hay que preocuparse si las páginas están en el lugar incorrecto. Una vez que se ha conseguido el nivel de zoom que mejor se ajusta al libro, se debe apretar el botón de "hecho" (done). La configuración de zoom es guardada en el dispositivo externo de almacenamiento, así que en la medida en que se continúe utilizando el mismo dispositivo externo de almacenamiento, no será necesario re-ajustar las configuraciones de zoom.

1. (Opcional). El tiempo de exposición puede ser configurado para cada cámara. Si de manera persistente las fotos están sobreexpuestas o subexpuestas, hay que trabajar con el tiempo de exposición.

1. Para asegurarse que el foco es consistente en todas las tomas, Pi Scan hará auto-foco una vez por cada sesión, y luego bloqueará ese foco para el resto de las tomas. Para obtener el mejor foco, será necesario presionar dos páginas contra la platina del escáner, tal como si se estuviera escaneando el libro, y luego apretar el botón de "reenfocar" (refocus). Se debe verificar en la vista previa (preview) que el foco es bueno. También se debe verificar que la página par del sistema está apuntando efectivamente a una página numerada par en el libro, y que la página impar del sistema está apuntando a una página impar del libro. Si no lo están, se puede apretar el botón de intercambio (swap) para cambiar las dos páginas. Esto asegurará que las páginas son intercaladas de la manera correcta durante la digitalización.

1. Durante la digitalización, se deben presionar las páginas contra la platina y apretar el botón de "captura" (capture). Luego de oír los disparos de las cámaras, se puede dar vuelta las páginas para pasar a las siguientes, mientras Pi Scan procesa las fotos. En la primera toma, es recomendable chequear que todo se ve bien. Y se debe hacer periódicamente a medida que se digitaliza. Si se nota algún problema durante la digitalización, se pueden recapturar las dos últimas páginas con el botón de "recapturar" (rescan).

1. Una vez que la digitalización está completa, se deberá apretar el botón de "Hecho" (done), que los llevará a la pantalla de inicio. Desde ahí se puede remover el dispositivo extenro de almacenamiento y mover los archivos a la computadora. Si se va a digitalizar un libro en más de una sesión, Pi Scan continuará numerando las imágenes donde se las haya dejado. Si se remueve la carpeta de 'images' del dispositivo externo de almacenamiento, Pi Scan empezará nombrando las páginas a partir del 0, es decir, como '0000.jpg'.

## Resolución de fallas y errores

En un mundo ideal, no deberíamos lidiar con esto. Hay algunas formas en que las cosas pueden ir mal. Pi Scan fue diseñado para ser robusto en presencia de problemas. Cada vez que se muestra un error, el usuario debería ser capaz de retomar la digitalización con el mínimo posible de confusión. Y los registros y mensajes de error que muestra el sistema debería permitir diagnosticar cualquier problema que aparezca en el proceso.

### Falla en la captura

A veces una cámara puede devolver una fotografía vacía o bien no capturar una imagen exitosamente. Cuando esto sucede, Pi Scan notificará al usuario y ninguna imagen de la cámara será guardada en el disco. Se debe apretar el botón de "ok" en la notificación y luego el botón de "captura" (capture) para intentarlo nuevamente. Si se advierte que esto sucede con más frecuencia, es necesario anotar el error y notificar a help at tenrec dot builders sobre el problema. Ocasionalmente, una cámara puede entrar en un estado raro luego de varios intentos fallidos de captura. Si fallan varias capturas seguidas, lo mejor es probar apagando y volviendo a encender la cámara a mano.

### Camera Crash

Ocasionalmente, una cámara tendrá algún conflicto interno o se desconectará. Pi Scan no puede notar la diferencia entre estos dos eventos, así que siempre asumirá que desconectar la cámara es un conflicto interno. Cuand Pi Scan piensa que ha habido un evento de este tipo, aparecerá una pantalla de debugeo. Este registro dirá qué cámara se desconectó, y la última actividad que estaba tratando de ejecutar cuando falló. En ese caso, se reconecta o se vuelve a encender la cámara, y el proceso detectará que la cámara está de vuelta conectada. Cuando la cámara está de vuelta, se puede apretar el botón de "obtener el registro de error" (Get Debug Log) y salvará el registro de debugeo para el fallo más reciento al dispositivo externo de almacenamiento, dentro del directorio de [debug]. Se puede enviar este registro de debug con el mensaje de error que apareció en la pantalla de debug a help at tenrec dot builders.

Una vez que las cámaras están conectadas de nuevo, se puede apretar 'Ok' para volver a la digitalización. Será necesario pasar por la pantalla de reenfoque (refocus) nuevamente para asegurarse que el foco está configurado correctamente.

### Pi Scan Crash

Con algo de suerte, nunca se verá una situación de Pi Scan en sí mismo falla, pero si esto sucede, hay una página especial de [debug] que muestra qué sucedió exactamente. Se puede tomar una fotografía de esta pantalla y enviarla a help at tenrec dot builders para reparar el fallo.

### Registro de error

Un registro de error es almacenado en el dispositivo externo de almacenamiento de cada fallo de la cámara. Esto quiere decir que incluso si se aprieta el botón de 'ok' rápidamente y se pierde el mensaje, aún así se puede volver atrás y recuperarlo. Si se están teniendo problemas o fallas persistentes, vale la pena enviar este registro de errores a help at tenrec dot builders para buscar una solución.

### Reinicio del sistema

Es bueno recordar siempre que Pi Scan no se daña por reiniciar la Raspberry. Por lo tanto, si hay algún problema o el sistema deja de responder, siempre se puede desconectar y reconectar la Raspberry Pi y luego volver a la digitalización del libro. Si se hace esto, será necesario chequear dos veces para asegurarse que las digitalizaciones que se hayan guardado en el dispositivo externo de almacenamiento estén bien porque el dispositivo no ha sido desmontado correctamente.

# Luego de la captura

Pi Scan solo hace una parte de todo el flujo de trabajo de la digitalización: gestiona la captura. Luego de utilizar Pi Scan, el resultado final será una tarjeta de memoria o un dispositivo externo de almacenamiento (lo que sea que se haya utilizado) lleno de archivos JPEG nombrados consecutivamente. Convertir estos archivos en un e-book se consigue mediante un proceso llamado post-proceso. Hay diversos tipos de software que pueden ayudar al usuario a hacer esta tarea. Una buena herramienta de software libre para realizar este trabajo es el ScanTailor.

# Notas de cada versión

- 1.0 -- Agregado el ajuste de tiempo de exposición, soporte para el disparador vía GPIO, soporte completo para teclado, soporte para pantalla táctil, un mecanismo de actualización, ejecución de un sonido para el error, gestión del foco en paralelo con el zoom, fallas diversas, y más. 
- 0.7 -- Agregado la numeración de páginas durante la captura. Arregladas las configuraciones de tiempo de exposición e ISO. Intento de arreglar los conflictos de las cámaras cuando entran en modo alt. Agregadas la detección de conflictos de Pi Scan para la previsualización y camera threads.
- 0.6 -- Arreglada la rotación en el modo previsualización. Las imágenes se mostraban dadas vueltas.
- 0.5 -- Arreglados algunos problemas con la numeración de las páginas. Se añadió la interfaz de usuario para ajustar el zoom.
- 0.4 -- Detecta cuando los directorios /debug e /images no se crean y notifica del problema en la pantalla de almacenamiento.
- 0.3 -- Se añadió más detección de erorres y una pantalla que muestra el error en caso de que ocurran excepciones inesperadas.
- 0.2 -- Se arregló un problema con espacios en los nombres de ruta y al escribir los registros de errores.
- 0.1 -- Lanzamiento inicial.
