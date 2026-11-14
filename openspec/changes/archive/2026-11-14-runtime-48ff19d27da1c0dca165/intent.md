# Intent: Make bulk price refresh fast and cheap with batched lookups and skip-if-fresh

## Problem

Refrescar los precios de toda la colección es lento y costoso: hoy se consulta la fuente de precios carta a carta por lotes, y con colecciones grandes tarda mucho y gasta muchas peticiones.

## Outcome

El usuario puede refrescar los precios de toda su colección en poco tiempo y con muchas menos peticiones a la fuente de precios, sin repetir trabajo ya hecho.

## Hypothesis

Creemos que reducir las consultas redundantes y actualizar solo lo necesario hará que el refresco completo sea notablemente más rápido y barato; lo sabremos al medir tiempo y número de peticiones por actualización sobre la misma colección.

## How we will know

- Una actualización completa de la misma colección tarda menos que con el sistema actual
- El número de peticiones a la fuente de precios por actualización baja de forma medible
- Cada carta registra la fecha de su último precio actualizado
- Relanzar la actualización justo después no repite el trabajo ya hecho

## Who and what it affects

- Job update_prices (backend/api/routes/process.py, backend/api/services/processor_service.py, deckdex/magic_card_processor.py)
- Historial de precios
- Pantalla desde donde el usuario lanza la actualización

## Constraints

- Debe convivir con los cambios de OpenSpec ya abiertos sobre precios (price-update-progress-resume y buffered-price-updates-verification)
- No debe bloquear el resto de la aplicación mientras corre

## Open questions

- ¿Cuál es la fuente de precios actual y qué límites de uso tiene?
- ¿Cuántas cartas tiene una colección típica o la tuya?
- ¿Los cambios de OpenSpec abiertos ya cubren parte de esto?
