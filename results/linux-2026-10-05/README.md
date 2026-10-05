# Full Linux suite validation

All 43 scenarios passed native recording and exact replay on Linux x86_64.
The test host used Ubuntu 24.04. The final run used source commit
`9705b740a71f58676b0ce4e76edbc526140e6571` with diagnostic tracing off.

The [workflow run](https://github.com/DanielTea/generalgamebench/actions/runs/37308967750)
passed all ten runtime groups and the final coverage check.
The [validation report](linux-validation.json) lists every scenario and its replay result.
The coverage check rejects missing scenarios, duplicates, and mixed source versions.
Each runtime group also passed its native goal and regression checks.

The [Linux fix](https://github.com/DanielTea/generalgamebench/pull/17) was merged as
`b8f273432ba0c34d6bd519db5435b6f364211514`.
Use the [Linux installation guide](../../environments/linux/README.md) to run the suite.
The full suite requires x86_64. The ten-scenario portable suite also supports ARM64.
