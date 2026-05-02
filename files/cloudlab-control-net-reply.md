# Reply to CloudLab admin re: control-network traffic

**To:** `<CloudLab admin contact, fill in from email header>`
**From:** Jason Cusati `<djjay@vt.edu>`
**Re:** Unusual control-network traffic on CS620426SP r650 reservations

Hi,

Thanks for the heads-up. I'm Jason Cusati, the user on the
`CS620426SP` project responsible for the recent r650 Clemson
reservations (most recently the May 1–2 experiment `prb-145800` with
nodes `clnode257` and `clnode263`).

## What we were doing

We are reproducing CHIME (SOSP '24) and porting its index from RDMA
to CXL-attached memory for a Virginia Tech CS 6204 final project. On
May 1–2 the experiment ran:

- a CHIME-RDMA throughput-thread sweep across YCSB C/D/E,
- a CHIME-CXL throughput-thread sweep (single-process, NUMA-emulated),
- competitor sweeps for SMART, ROLEX, and Sherman,
- a CXL fig\_15a cumulative-feature ablation.

All experiment software was correctly bound to the internal RDMA LAN:
- `memcached.conf` was set to `10.10.1.1:11211` (internal `vlan296`),
- RDMA `ib_post_send` traffic ran over `vlan296` (10.10.1.x, MTU 9000),
- CXL emulation was single-process on `clnode257` (no network at all).

We can confirm from `/proc/net/dev` and `ifconfig` snapshots that the
public-facing interface (`eno12399`) carried no experiment-side TCP
traffic.

## What likely caused the unusual control-net traffic

We believe the unusual traffic was on the **management side**, not the
experiment side. Specifically:

1. We ran an automated experiment driver from a laptop that polled
   the master node over SSH every 60–180 seconds for ~10 hours
   straight, so we could update plots in real time as sweeps
   completed. Each SSH handshake is ~10 KB on the public control net,
   and over the day this accumulates to several MB per node per
   reservation.
2. We also pulled experiment results back to the laptop via `scp`
   periodically.
3. At experiment startup we cloned three GitHub repos
   (`CHIME`, `SMART`, `ROLEX`) onto the master node, which fetched
   over the public network.

None of (1)-(3) are unusual one-off events on their own, but the
combination — sustained for ~10 hours — is what we think looked
unusual.

## What we will do differently

For the next reservation (May 6 onward, resgroup `8971e238`,
7 r650 nodes), we have committed the following changes to the
project repository (https://github.com/djjay0131/CHIME):

1. A `script/control-net-guard.sh` that runs **on the cluster
   node** and samples `/sys/class/net/<control_iface>/statistics/`
   counters every 10 seconds. It writes a small log to `/proj/`
   showing public-iface vs internal-iface byte rates and aborts
   the experiment if the public iface exceeds 1 MB per 10-second
   window during an experiment.
2. A new on-cluster experiment driver pattern: the experiment script
   writes its progress to a file on the master node, and we `scp`
   the file (one transfer) every 10 minutes from the laptop, instead
   of per-poll `ssh tail`.
3. A pre-flight check in the runbook that confirms `memcached.conf`
   and the RDMA iface are both internal (`10.x.x.x`) before any
   experiment binary is launched.

Happy to share any logs or the commit history if useful. Apologies for
the noise on the shared network, and thanks for the watchful eye.

Best,
Jason Cusati
PhD student, Virginia Tech

---

## Operational notes (separate from the email body)

To monitor experiment / reservation lifecycle without ssh-polling, we
will use:

- `script/cloudlab-status-watch.sh` — hits the portal API (no ssh)
  to list active reservations, experiments, and a UTC timeline.
  Usage:  `bash script/cloudlab-status-watch.sh [--watch]`.

- For email notifications from CloudLab (sent to `djjay@vt.edu`), set
  up a vt.edu → `djjay0131@gmail.com` forwarding rule for senders that
  match `support@cloudlab.us` and `*@flux.utah.edu`. Then in Gmail
  create a filter:

      From: support@cloudlab.us OR *@flux.utah.edu OR *@emulab.net
      → Apply label: CloudLab
      → Mark as important

  Once that label exists, the project's MCP-based pull script can
  fetch `label:CloudLab newer_than:7d` automatically.
