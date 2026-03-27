---
title: "Research Report"
subtitle: "Reproducing CHIME: A Cache-Efficient and High-Performance Hybrid Index on Disaggregated Memory"
---

CS 6204 Advanced Topics in Systems — Virginia Tech, Spring 2026.

**Download:** <a href="/CHIME/pdfs/Jason_Cusati_Project_Part_One.pdf">Jason_Cusati_Project_Part_One.pdf</a>

{{< pdf "/pdfs/Jason_Cusati_Project_Part_One.pdf" >}}

---

## Report Summary

This progress report documents our effort to reproduce experiments from the CHIME paper (SOSP '24) on CloudLab infrastructure. It covers:

1. **Experiments planned** — Figures 12, 14, 15a, 15b from the paper, plus three additional sensitivity studies
2. **CloudLab reservation challenges** — r650 unavailability pre-deadline, alternative r6525 attempt
3. **r6525 hardware experience** — 11 issues diagnosed across RDMA device selection, RoCE compatibility, disk space, Paramiko SSH, and memcached coordination
4. **r650 run plan** — Automated setup for March 27–April 3, with pre-generated workloads on NFS
5. **Part Two direction** — Porting CHIME to CXL-based disaggregated memory

*Full experimental results will be added after the r650 run (March 27–April 3).*
