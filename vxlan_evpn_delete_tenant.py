''' vxlan_evpn_delete_tanant.py 1.0 - This script will delete a tenant on the leaf switches.  The tenant name and other
 parameters should be specified in the tenant.csv file.  The format of tenant.csv should be:

TENANT_NAME, VLAN_ID, L2_VNID, L3_VNI_VLAN, L3_VNID, IP_ADDR, BGP_AS

TENANT_NAME = Name of the tenant to be deleted
VLAN_ID - VLAN associated with this tenant
L2_VNID - The VXLAN segment-id associated with the VLAN_ID
L3_VNI_VLAN - The VLAN used for the L3_VNI of the tenant
L3_VNID - The VXLAN segment-id  associated with the L3_VNI_VLAN
IP_ADDR - The IP address assigned to the SVI that will be created for VLAN_ID (not used here)
BGP_AS - The BGP AS in use on each leaf switch (script is assuming iBGP,  script will not work with eBGP)

The script will connect to each leaf IP address as specified in the leaf.csv file.  Format of the leaf.csv file should
have each leaf switch IP address on a separate line. For example:

10.255.139.185
10.255.139.186
10.255.139.147

Any questions, problems, or suggestions please contact Matt Mullen (matt.mullen@wwt.com)

'''

import requests
import json
import sys

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

# Store each value in tenant.csv into variables
try:
    TENANT_NAME, VLAN_ID, L2_VNID, L3_VNI_VLAN, L3_VNID, IP_ADDR, BGP_AS = tenant_list[1].split(',')
except:
    print('''Error parsing the tenant.csv file,  please make sure the file is in the format:
    TENANT_NAME, VLAN_ID, L2_VNID, L3_VNI_VLAN, L3_VNID, IP_ADDR, BGP_AS)''')

# This is the userid/password that will be used to access the devices.
switchuser='demouser'
switchpassword='WWTwwt1!'


# List of commands that will be posted to device. Note that some commands must be posted together. Commands that must
# be posted together are included together in a tuple inside the list.
cmds = [('interface nve1',
'no member vni {0} associate-vrf'.format(L3_VNID)),
('router bgp {0}'.format(BGP_AS),
'no vrf {0}'.format(TENANT_NAME)),
"no interface Vlan{0}".format(L3_VNI_VLAN),
"no vlan {0}".format(L3_VNI_VLAN),
"no vrf context {0}".format(TENANT_NAME)
]

vlans = set([])

# Interrogate the switches to determine VLANs added under the tenant
for leaf in leaf_switches:
    myheaders={'content-type':'application/json'}
    url='http://{0}/ins'.format(leaf.strip())
    payload={
      "ins_api": {
        "version": "1.0",
        "type": "cli_show",
        "chunk": "0",
        "sid": "1",
        "input": "show ip interface brief vrf {0}".format(TENANT_NAME),
        "output_format": "json"
      }
    }
    try:
        response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()
    except:
        print('''There was an error '{0}' connecting to {1}. Please ensure the switches are reachable and NXAPI is turned on.
        Also make sure userid demouser with password WWTwwt1! is created with network-admin role'''.format(sys.exc_info(),leaf))
        quit()
    if 'TABLE_intf' in response['ins_api']['outputs']['output']['body']:
        intf_list = response['ins_api']['outputs']['output']['body']['TABLE_intf']
        if isinstance(intf_list,list):
            for line in intf_list:
                vlans.add(line['ROW_intf']['intf-name'].strip('Vlan'))
        else:
            vlans.add(intf_list['ROW_intf']['intf-name'].strip('Vlan'))

# Interrogate the switches again,  this time to determine the VLAN to VXLAN segment-id mapping and store in a dict
for leaf in leaf_switches:
    myheaders={'content-type':'application/json'}
    url='http://{0}/ins'.format(leaf.strip())
    payload={
      "ins_api": {
        "version": "1.0",
        "type": "cli_show_ascii",
        "chunk": "0",
        "sid": "1",
        "input": "show vxlan",
        "output_format": "json"
      }
    }
    try:
        response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()
    except:
        print('''There was an error '{0}' connecting to {1}. Please ensure the switches are reachable and NXAPI is turned on.
        Also make sure userid demouser with password WWTwwt1! is created with network-admin role'''.format(sys.exc_info(),leaf))
    vxlan_list = [x for x in response['ins_api']['outputs']['output']['body'].split('\n')]
    vxlan_list.remove('')
    vxlan_dict = {}
    for line in vxlan_list:
        vlan_id,vxlan_id = line.split('  ')
        vxlan_dict[vlan_id] = vxlan_id

# Add the VLANs for deletion to the cmd list
for vlan in vlans:
    cmds.append(('interface nve1', 'no member vni {0}'.format(vxlan_dict[vlan])))
    cmds.append(('evpn', 'no vni {0} l2'.format(vxlan_dict[vlan])))
    cmds.append('no interface vlan {0}'.format(vlan))
    cmds.append('no vlan {0}'.format(vlan))

def sendcmd(leaf,cmd):
    ''' This function will send a command, or group of commands to the device and return the response '''
    if isinstance(cmd,tuple):
        payload = []
        for i in range (0,len(cmd)):
            payload.append({
                "jsonrpc": "2.0",
                "method": "cli",
                "params": {
                    "cmd": cmd[i],
                    "version": 1
                },
                "id": i
            })
    else:
        payload=[
          {
            "jsonrpc": "2.0",
            "method": "cli",
            "params": {
              "cmd": cmd,
              "version": 1
            },
            "id": 1
          }
        ]
    url='http://{0}/ins'.format(leaf.strip())
    myheaders={'content-type':'application/json-rpc'}
    try:
        response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()
    except:
        print('''There was an error '{0}' connecting to {1}. Please ensure the switches are reachable and NXAPI is turned on.
        Also make sure userid demouser with password WWTwwt1! is created with network-admin role'''.format(sys.exc_info(),leaf))
    return payload, response

def findcmd(payld,id):
    ''' This function searches the JSON payload for the id provided in the response and returns the command associated
    with that id'''
    for i in range (0,len(payld)):
        if payld[i]['id'] == id:
            cmd = payld[i]['params']['cmd']
    return cmd

def printmsg(s1, s2):
    ''' This function is used to print the command and any message that was received from the switch'''
    print ('While processing command: {0}, got message {1}'.format(s1,s2))



# Begin main program execution,  loop through switches and run the commands
for leaf in leaf_switches:
    print("Processing leaf: {0}".format(leaf))

    for cmd in cmds:
        payload, response = sendcmd(leaf,cmd)
        # return from sendcmd() will be a dict if a single command,  or a list of dicts if a tuple
        if isinstance(response,list):
            for item in response:
                if 'result' in item:
                    if item['result']:
                        c = findcmd(payload,item['id'])
                        printmsg(c, item['result']['msg'])
                if 'error' in item:
                    if 'data' in item['error']:
                        c = findcmd(payload,item['id'])
                        printmsg(c, item['error']['data']['msg'])
                    if not 'data' in item['error'] and 'message' in item['error']:
                        c = findcmd(payload, item['id'])
                        printmsg(c, item['error']['message'])
        else:
            if 'result' in response:
                if response['result']:
                    c = findcmd(payload,response['id'])
                    printmsg(c, response['result']['msg'])
            if 'error' in response:
                if 'data' in response['error']:
                    c = findcmd(payload,response['id'])
                    printmsg (c, response['error']['data']['msg'])
                if not 'data' in response['error'] and 'message' in response['error']:
                    c = findcmd(payload, response['id'])
                    printmsg (c, response['error']['message'])

print ("Complete!")






