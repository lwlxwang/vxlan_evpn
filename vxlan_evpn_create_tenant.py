''' vxlan_evpn_create_tanant.py 1.0 - This script will create a tenant on the leaf switches and an initial VLAN within
the new tenant.  The tenant name and other parameters should be specified in the tenant.csv file.  The format of
tenant.csv should be:

TENANT_NAME, VLAN_ID, L2_VNID, L3_VNI_VLAN, L3_VNID, IP_ADDR, BGP_AS

TENANT_NAME = Name you would like to assign to the new tenant
VLAN_ID - The initial VLAN to be created within this tenant
L2_VNID - The VXLAN segment-id to be associated with the VLAN_ID
L3_VNI_VLAN - The VLAN used for the L3_VNI of the tenant
L3_VNID - The VXLAN segment-id to be associated with the L3_VNI_VLAN
IP_ADDR - The IP address to assign to the SVI that will be created for VLAN_ID
BGP_AS - The BGP AS in use on each leaf switch (script is assuming iBGP,  script will not work with eBGP)

The script will connect to each leaf IP address as specified in the leaf.csv file.  Format of the leaf.csv file should
have each leaf switch IP address on a separate line. For example:

10.255.139.185
10.255.139.186
10.255.139.147

Any questions, problems, or suggestions please contact Matt Mullen (matt.mullen@wwt.com)

'''
import sys
import requests
import json

# Open the files and store the contents
try:
    with open('tenant.csv','r') as f:
        tenant_list = f.readlines()
except:
    print("Error opening tenant.csv file,  please ensure tenant.csv is present in the same directory as this script.")
    quit()

try:
    with open('leaf.csv','r') as f:
        leaf_switches = f.readlines()
except:
    print("Error opening leaf.csv, please ensure leaf.csv is present in the same directory as this script.")
    quit()

# Store each value in tenant.csv into variables, skipping first line
try:
    TENANT_NAME, VLAN_ID, L2_VNID, L3_VNI_VLAN, L3_VNID, IP_ADDR, BGP_AS = tenant_list[1].split(',')
except:
    print('''Error parsing the tenant.csv file,  please make sure the file is in the format:
    TENANT_NAME, VLAN_ID, L2_VNID, L3_VNI_VLAN, L3_VNID, IP_ADDR, BGP_AS)''')

# This is the userid/password that will be used to access the devices.
switchuser='demouser'
switchpassword='WWTwwt1!'

myheaders={'content-type':'application/json-rpc'}

# Below is the JSON payload that will be posted to the switch, with the variables filling in the parameters where required.
payload = [
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "vlan {0}".format(VLAN_ID),
      "version": 1
    },
    "id": 1
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  name {0}_VL{1}".format(TENANT_NAME, VLAN_ID),
      "version": 1
    },
    "id": 2
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  vn-segment {0}".format(L2_VNID),
      "version": 1
    },
    "id": 3
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "vlan {0}".format(L3_VNI_VLAN),
      "version": 1
    },
    "id": 4
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  name L3-vni-vlan-for-{0}".format(TENANT_NAME),
      "version": 1
    },
    "id": 5
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  vn-segment {0}".format(L3_VNID),
      "version": 1
    },
    "id": 6
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "vrf context {0}".format(TENANT_NAME),
      "version": 1
    },
    "id": 7
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  vni {0}".format(L3_VNID),
      "version": 1
    },
    "id": 8
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  rd auto",
      "version": 1
    },
    "id": 9
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  address-family ipv4 unicast",
      "version": 1
    },
    "id": 10
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "    route-target import {0}:{1}".format(L3_VNID,L3_VNID),
      "version": 1
    },
    "id": 11
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "    route-target export {0}:{1}".format(L3_VNID,L3_VNID),
      "version": 1
    },
    "id": 12
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "    route-target both auto",
      "version": 1
    },
    "id": 13
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "    route-target both auto evpn",
      "version": 1
    },
    "id": 14
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": " interface Vlan{0}".format(VLAN_ID),
      "version": 1
    },
    "id": 15
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  no shutdown",
      "version": 1
    },
    "id": 16
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  vrf member {0}".format(TENANT_NAME),
      "version": 1
    },
    "id": 17
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  ip address {0}/24".format(IP_ADDR),
      "version": 1
    },
    "id": 18
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  fabric forwarding mode anycast-gateway",
      "version": 1
    },
    "id": 19
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "interface Vlan{0}".format(L3_VNI_VLAN),
      "version": 1
    },
    "id": 20
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  description L3-vni-for-{0}-Routing".format(TENANT_NAME),
      "version": 1
    },
    "id": 21
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  no shutdown",
      "version": 1
    },
    "id": 22
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  vrf member {0}".format(TENANT_NAME),
      "version": 1
    },
    "id": 23
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "interface nve1",
      "version": 1
    },
    "id": 24
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  member vni {0}".format(L2_VNID),
      "version": 1
    },
    "id": 25
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "    suppress-arp",
      "version": 1
    },
    "id": 26
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "    ingress-replication protocol bgp",
      "version": 1
    },
    "id": 27
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  member vni {0} associate-vrf".format(L3_VNID),
      "version": 1
    },
    "id": 28
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "router bgp {0}".format(BGP_AS),
      "version": 1
    },
    "id": 29
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "vrf {0}".format(TENANT_NAME),
      "version": 1
    },
    "id": 30
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "    address-family ipv4 unicast",
      "version": 1
    },
    "id": 31
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "      advertise l2vpn evpn",
      "version": 1
    },
    "id": 32
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "evpn",
      "version": 1
    },
    "id": 33
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "  vni {0} l2".format(L2_VNID),
      "version": 1
    },
    "id": 34
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "    rd auto",
      "version": 1
    },
    "id": 35
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "    route-target import auto",
      "version": 1
    },
    "id": 36
  },
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "    route-target export auto",
      "version": 1
    },
    "id": 37
  }
]

def findcmd(payld,id):
    ''' This function searches the JSON payload for the id provided in the response and returns the command associated
    with that id'''
    for i in range (0,len(payld)):
        if payld[i]['id'] == id:
            cmd = payld[i]['params']['cmd']
    return cmd

# Begin processing each leaf in leaf.csv
for leaf in leaf_switches:
    print("Processing leaf: {0}".format(leaf))
    url='http://{0}/ins'.format(leaf.strip())
    response = []
# Post the JSON to the leaf and store the response
    try:
        response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()
    except:
        print('''There was an error '{0}' connecting to {1}. Please ensure the switches are reachable and NXAPI is turned on.
        Also make sure userid demouser with password WWTwwt1! is created with network-admin role'''.format(sys.exc_info(),leaf))
# Search the response to see if we had any errors or informational messages,  and print them
    for element in response:
        if 'result' in element:
            cmd = findcmd(payload,element['id'])
            if element['result']:
                print ("While processing command: {0}, got message {1}".format(cmd,element['result']['msg']))
        if 'error' in element:
            if 'data' in element['error']:
                cmd = findcmd(payload,element['id'])
                print ("While processing command: {0}, got message {1}".format(cmd,element['error']['data']['msg']))
            if not 'data' in element['error'] and 'message' in element['error']:
                cmd = findcmd(payload,element['id'])
                print ("While processing command: {0}, got message {1}".format(cmd,element['error']['message']))



print('Complete!')
