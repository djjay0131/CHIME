"""CloudLab profile: r650 nodes with internal LAN for RDMA.

Creates N r650 nodes at Clemson connected by a shared internal LAN.
RDMA (RoCE) traffic goes over the internal 10.x.x.x network,
not the public control network.

Instructions:
  - Use the internal IPs (10.x.x.x from /etc/hosts) for memcached and RDMA.
  - The internal interface name will be shown in /etc/hosts or via `ip addr`.
  - Do NOT use the public-facing eno12399 interface for RDMA traffic.
"""

import geni.portal as portal
import geni.rspec.pg as pg

pc = portal.Context()

# Parameters
pc.defineParameter("n", "Number of nodes", portal.ParameterType.INTEGER, 6)
pc.defineParameter("hw", "Hardware type", portal.ParameterType.STRING, "r650",
                   [("r650", "r650 (Intel Xeon, Clemson)"),
                    ("r6525", "r6525 (AMD EPYC, Clemson)")])

params = pc.bindParameters()

request = pc.makeRequestRSpec()

# Create a shared LAN for internal RDMA traffic
lan = request.LAN("rdma-lan")
lan.best_effort = True
lan.vlan_tagging = True
lan.link_multiplexing = True

for i in range(params.n):
    node = request.RawPC("node%d" % i)
    node.hardware_type = params.hw
    node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD"
    node.component_manager_id = "urn:publicid:IDN+clemson.cloudlab.us+authority+cm"

    # Add interface to internal LAN
    iface = node.addInterface("if1")
    iface.addAddress(pg.IPv4Address("10.10.1.%d" % (i + 1), "255.255.255.0"))
    lan.addInterface(iface)

pc.printRequestRSpec(request)
