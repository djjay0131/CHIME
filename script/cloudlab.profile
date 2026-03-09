"""10 r650 instances for running CHIME (Clemson cluster)"""

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

pc = portal.Context()
request = pc.makeRequestRSpec()

CLEMSON_CM = "urn:publicid:IDN+clemson.cloudlab.us+authority+cm"
NODE_COUNT = 10
IMAGE = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD"

ifaces = []
for i in range(NODE_COUNT):
    node = request.RawPC("node-%d" % i)
    node.routable_control_ip = True
    node.hardware_type = "r650"
    node.disk_image = IMAGE
    node.component_manager_id = CLEMSON_CM
    iface = node.addInterface("interface-%d" % i)
    ifaces.append(iface)

link = request.Link("link-0")
for iface in ifaces:
    link.addInterface(iface)

pc.printRequestRSpec(request)
