## 1. i18n keys

- [x] 1.1 Add `cardTable.importList` key to `frontend/src/locales/en.json` with value "Import list"
- [x] 1.2 Add `cardTable.importList` key to `frontend/src/locales/es.json` with value "Importar lista"

## 2. CardTable component

- [x] 2.1 Add `onImport` optional callback prop to CardTable component
- [x] 2.2 Add "Import list" outline button next to "Add card" in the toolbar, rendered when `onImport` is provided
- [x] 2.3 Style button as indigo outline/ghost with dark mode support

## 3. Dashboard wiring

- [x] 3.1 Pass `onImport` callback from Dashboard to CardTable using `useNavigate` to navigate to `/import`
