## 1. i18n

- [x] 1.1 Add `cardTable.updatePrices` to `en.json` ("Update Prices") and `cardTable.starting` ("Starting...")
- [x] 1.2 Add `cardTable.updatePrices` to `es.json` ("Actualizar precios") and `cardTable.starting` ("Iniciando...")

## 2. Settings cleanup

- [x] 2.1 In `SettingsModal.tsx`, remove the "Go to import" button and description from the Import Collection section; promote Quick Import as direct section content (remove `<details>` wrapper)
- [x] 2.2 Remove the entire Deck Actions section (`<section>` with `ActionButtons`) from SettingsModal
- [x] 2.3 Remove unused imports in SettingsModal (`navigate`, `ActionButtons`, etc.) if no longer needed

## 3. CardTable Update Prices button

- [x] 3.1 Add `onUpdatePrices` and `updatingPrices` optional props to CardTable
- [x] 3.2 Render "Update Prices" button in toolbar when `onUpdatePrices` is provided, styled as slate/gray outline (tertiary)
- [x] 3.3 Show "Starting..." text and disable button when `updatingPrices` is true

## 4. Dashboard wiring

- [x] 4.1 Import `useTriggerPriceUpdate` and `useActiveJobs` in Dashboard; create `handleUpdatePrices` callback
- [x] 4.2 Pass `onUpdatePrices` and `updatingPrices` props from Dashboard to CardTable
