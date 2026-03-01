## 1. Backend: Import endpoints accept text input

- [x] 1.1 In `backend/api/routes/import_routes.py`, change `POST /api/import/preview` to accept `file: Optional[UploadFile] = File(None)` and `text: Optional[str] = Form(None)`. If `text` is non-empty, parse with MTGO parser and return `detected_format: "mtgo"`. If `file`, use existing `_parse_file` logic. If neither, raise 400.
- [x] 1.2 In `backend/api/routes/import_routes.py`, change `POST /api/import/external` to accept `file: Optional[UploadFile] = File(None)` and `text: Optional[str] = Form(None)`. If `text`, parse with MTGO parser. If `file`, existing logic. If neither, raise 400.

## 2. Backend: GET /api/jobs includes DB-persisted running jobs

- [x] 2.1 Add `user_id: int = Depends(get_current_user_id)` to `GET /api/jobs` in `backend/api/routes/process.py`.
- [x] 2.2 After building the in-memory job list, call `job_repo.get_job_history(user_id, limit=20)`. Append jobs with `status in ('running', 'pending')` whose IDs are not already in the response. Wrap in `try/except` to not break if DB is unavailable.

## 3. Frontend: API client methods for text import

- [x] 3.1 Add `importPreviewText(text: string)` to `frontend/src/api/client.ts`. Sends `FormData` with `text` field to `POST /api/import/preview`. Same response type as `importPreview`.
- [x] 3.2 Add `importExternalText(text: string, mode: 'merge' | 'replace')` to `frontend/src/api/client.ts`. Sends `FormData` with `text` and `mode` fields to `POST /api/import/external`. Same response type as `importExternal`.

## 4. Frontend: Import wizard text paste tab

- [x] 4.1 Add `InputMode = 'file' | 'text'` type and `inputMode` / `pastedText` state to `Import.tsx`.
- [x] 4.2 Add a two-button tab switcher at the top of the Step 1 panel: "Subir archivo" and "Pegar texto". Active tab has blue background.
- [x] 4.3 When `inputMode === 'text'`, render a `<textarea>` (10 rows, monospace, with placeholder showing example format) and a "Continuar →" button that calls `handleTextPreview()`.
- [x] 4.4 Add `handleTextPreview()` that calls `api.importPreviewText(pastedText)` and advances to preview step on success.
- [x] 4.5 Update `handleImport()` to branch on `inputMode`: calls `api.importExternalText(pastedText, mode)` when in text mode, `api.importExternal(file!, mode)` when in file mode.
- [x] 4.6 Update `reset()` to clear `pastedText` state alongside `file`.
