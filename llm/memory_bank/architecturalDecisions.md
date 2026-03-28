# Architectural Decisions

## ADR-001: Mirror the Proposal Project's Documentation Layout

Status: accepted

Decision: Create `construction/` and `memory-bank/` (now `llm/memory_bank/`) with the same workflow concepts as `construction-ai-proposal`, adapted for code comprehension and repository stewardship.

## ADR-002: Center Initial Code Documentation on One Figure Script

Status: accepted

Decision: Use `exp/fig_03a.py` as the representative experiment walkthrough for the first documentation pass, covering the main orchestration pattern.

## ADR-003: Pivot Pre-Deadline Run to r6525 Nodes

Status: accepted

Decision: Run pre-deadline experiments on 11x r6525 at Clemson (reservation 83cd62fd) despite hardware differences (AMD vs Intel, different NICs). r650 dry-run expired unused and r650 was fully booked until Mar 27. Follow up with r650 runs for hardware-matched data.

Consequences: CPU_PHYSICAL_CORE_NUM=64, public IPs in memcached.conf, 16GB root partition requires NVMe/NFS. ibv_exp_dct confirmed working.

## ADR-004: Persist YCSB Workloads on Project NFS

Status: accepted

Decision: Store YCSB workloads on CloudLab project NFS (`/proj/cs620426sp-PG0/ycsb_workloads/`) and symlink from `~/CHIME/ycsb/workloads`. Workloads generated once (~1.5h), reused across all experiment instances.
