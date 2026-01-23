# Attachment Service

This service provides local storage for attachments used by the tracking endpoints.

Configuration

- `ATTACHMENTS_DIR` (env) - local directory where files are stored (default: `attachments`)
- `ATTACHMENT_BASE_URL` (env) - base URL exposed by the app for attachments (default: `/attachments`)

Behavior

- `AttachmentService.save_file(bytes, original_name)` saves the file and returns `{ "url": "<base_url>/<filename>", "path": "<path>", "filename": "<filename>" }`.
- `save_base64` accepts base64-encoded data and stores it.
- For now the implementation is local-only (no S3). If S3 is desired in the future we can add a backend switch and use `boto3`.

Usage

- The `/api/v2/shipments/{shipment_id}/status` endpoint accepts attachments in two ways:
  - JSON body field `attachments` (or `anexos` for backward compatibility): list of objects shaped as `{ "arquivo": { "dados": "<Base64>", "nome": "optional" } }`.
  - Multipart form-data: one or more files under the field name `attachment` and a form field `novo_status_json` (or `new_status`) containing the status JSON.

- When attachments are processed they are hosted under the configured `ATTACHMENT_BASE_URL` and the VBLOG payload receives an `anexos` array with `{ "arquivo": { "nome": "<url>", "dados": "<Base64>" } }`.
