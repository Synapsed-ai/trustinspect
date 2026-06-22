# TrustInspect Target Registry Cleanup

TrustInspect loads built-in and local targets from two locations:

- `examples/targets/` for built-in targets shipped with the project.
- `targets/local/` for targets calibrated on the tester machine.

If the interactive launcher shows duplicates, it usually means the same target exists both as a built-in target and as a local calibrated target.

Use:

```bash
python scripts/list_targets.py
python scripts/clean_target_registry.py --dry-run
python scripts/clean_target_registry.py --apply
```

The cleanup command moves disabled/duplicate targets to `targets/_disabled/<timestamp>/` instead of deleting them.
