# Intent: Corregir la incompatibilidad de dependencias que impide arrancar el backend en Docker

## Problem

El backend de deckdex falla durante las migraciones con un error de módulo psycopg ausente e impide utilizar la aplicación local.

## Outcome

El backend arranca de forma reproducible y se conecta a PostgreSQL con las dependencias de una imagen recién construida.

## Hypothesis

Resolver la incompatibilidad entre las dependencias de base de datos permitirá completar las migraciones y arrancar el backend.

## How we will know

- Una imagen recién construida completa las migraciones sin ModuleNotFoundError de psycopg.
- El backend inicia y responde a su comprobación de salud.

## Who and what it affects

- Backend de deckdex
- Arranque local con Docker

## Constraints

- Aplicar un arreglo permanente en el repositorio.
- Conservar los datos existentes de PostgreSQL.
- Limitar el cambio al fallo de arranque y sus comprobaciones.

## Open questions

- Validar la causa exacta de la selección del driver antes de aplicar el arreglo.
