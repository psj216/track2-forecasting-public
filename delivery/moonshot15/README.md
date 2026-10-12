## Executive summary (read this first)

This bundle packs five immutable M15 Development candidates on your own Windows computer. It never uploads anything and never reads or stores a Team Key. Keep your existing V51-final-submission.zip unchanged.

1. Extract this bundle to a new folder. Do not mix it with Final files.
2. Open the same PowerShell/environment in which official qfbench2-common2.6.0 was installed. Python must be3.13 or later.
3. Run, replacing N with your verified website team number:

```powershell
python .\pack_five.py --team-number N
```

No Git or Docker installation is required for packing. The helper finds qfbench2.exe on PATH or next to Python. It checks toolkit2.6.0 and every draft before invoking the official CLI.

Enter the same Team Key in each official hidden prompt. The helper does not read it, pass it on the command line, redirect it, or save it. If the official CLI refuses a terminal that cannot hide input, stop and run in a normal local PowerShell terminal. Do not paste the key into Work.

Output directory: M15-development-packages, containing M15-A-development.zip through M15-E-development.zip and M15-package-verification.json. Existing ZIPs are verified rather than overwritten. Delete an invalid new M15 ZIP yourself only if correcting a failed local pack; Final files must remain untouched.

Each package holds only submission.json and team-claim.json. Phase is dev, competition is agenthon2026-forecasting-dev. The exact House-model disclosure is included. These ZIPs are Development candidates, not proven alpha. Mock runtime tests cannot establish live House forecast quality or0.5 performance. Live stochastic House replies may vary even with temperature0; repeat tests establish deterministic transformations for the same reply, not deterministic service outputs.

After inspecting local verification, you may decide what to upload yourself within your remaining Development allowance. This bundle contains no upload command. Never use these Development ZIPs for Final.
