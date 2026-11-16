## Review checklist

<ul>
  <li>☑ Configuration defaults and feature gates match the implementation.</li>
  <li>☑ No real credentials, private keys, host-specific identifiers or personal data were added.</li>
  <li>☑ Operations have been reviewed for privilege, destructive effects and remote lockout risk.</li>
  <li>☑ Dry-run output has been reviewed on a suitable target.</li>
  <li>☑ <code>pre-commit run --all-files</code> passes.</li>
  <li>☑ <code>uv run pytest tests/ -v</code> passes.</li>
  <li>☑ README and relevant documentation have been updated.</li>
</ul>
