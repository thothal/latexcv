# private-repo-starter

This folder is a starter scaffold for your private CV data repository.

## Suggested Use

1. Move this folder outside of the tool repository.
2. Initialize a new private git repository.
3. Replace placeholder content in `data/*.yaml` with your real CV data.
4. Render with the tool:

```powershell
cv-render data --output-dir output --lang en
cv-render data --output-dir output --lang de
```

The schema follows the block/layout model used by the tool repository.
