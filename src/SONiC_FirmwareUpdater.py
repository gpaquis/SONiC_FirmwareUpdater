"""
Description: This script allow to upgrade remotely a switch using Dell Enterprise SONiC
Author: Gerald PAQUIS
Date Created: November 2023
Date Modified: December, 2023
Version: 0.6
Python Version: 3.8.10
Dependencies: none
License: GPL-3.0 license
"""


import json
import argparse
import ast
import requests
import configparser
import ipaddress
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth
import base64
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def validate_ip_address(ip_string) -> bool:
    try:
      ip_object = ipaddress.ip_address(ip_string)
      return True
    except ValueError:
      return False

def cancel_install(remote_sw):
    """
        Cancel installtion image
        By default REST api don't return the CRC state
        If the INSTALL_IDLE at 100% stay stuck after 500 cycles the install is canceled
        Until the REST API return is not update, use with caution
    """

    switch_ip = remote_sw['ip_switch']
    user_name = remote_sw['sonic_username']
    password = remote_sw['sonic_password']

    request_data = {
        "openconfig-image-management:input": {
        }
    }
    try:
       response = requests.post(url=f"https://{switch_ip}/restconf/operations/openconfig-image-management:image-install-cancel",
                                data=json.dumps(request_data),
                                headers={'Content-Type': 'application/yang-data+json'},
                                auth=HTTPBasicAuth(f"{user_name}", f"{password}"),
                                verify=False
                                )
       response.raise_for_status()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    else:
        mystatus = json.loads(response.content)
        myreturn = mystatus["openconfig-image-management:output"]["status-detail"]
        return myreturn

def rpcupdate(remote_sw, server_ip: str, method: str, firmware: str) -> str:
    """
        update firmware OS on SONiC OS
        Take Parmeter from the commande line
            method available:
                HTTP/S
    """

    image_name = method+"://"+server_ip+"/"+firmware
    print (f'Install image from : {image_name}')

    switch_ip = remote_sw['ip_switch']
    user_name = remote_sw['sonic_username']
    password = remote_sw['sonic_password']

    request_data = {
        "openconfig-image-management:input": {
           "image-name": image_name
        }
    }

    try:
       response = requests.post(url=f"https://{switch_ip}/restconf/operations/openconfig-image-management:image-install",
                                data=json.dumps(request_data),
                                headers={'Content-Type': 'application/yang-data+json'},
                                auth=HTTPBasicAuth(f"{user_name}", f"{password}"),
                                verify=False
                                )
       response.raise_for_status()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    else:
        mystatus = json.loads(response.content)
        myreturn = mystatus["openconfig-image-management:output"]["status-detail"]
        return myreturn

def bootswap(remote_sw, firmware: str) -> str:
    """
        Swap Boot Firmware
    """

    switch_ip = remote_sw['ip_switch']
    user_name = remote_sw['sonic_username']
    password = remote_sw['sonic_password']

    request_data = {
        "openconfig-image-management:input": {
           "image-name": firmware
        }
    }

    try:
       response = requests.post(url=f"https://{switch_ip}/restconf/operations/openconfig-image-management:image-default",
                                data=json.dumps(request_data),
                                headers={'Content-Type': 'application/yang-data+json'},
                                auth=HTTPBasicAuth(f"{user_name}", f"{password}"),
                                verify=False
                                )
       response.raise_for_status()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    else:
        mystatus = json.loads(response.content)
        myreturn = mystatus["openconfig-image-management:output"]["status-detail"]
        return myreturn

def check_status(remote_sw):
    """
       Check Firmware Status Upgrade
    """

    switch_ip = remote_sw['ip_switch']
    user_name = remote_sw['sonic_username']
    password = remote_sw['sonic_password']

    try:
       response = requests.get(url=f"https://{switch_ip}/restconf/data/openconfig-image-management:image-management",
                                headers={'Content-Type': 'application/yang-data+json'},
                                auth=HTTPBasicAuth(f"{user_name}", f"{password}"),
                                verify=False
                                )
       response.raise_for_status()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    else:
        #print (response.content)
        return_dict = dict();
        mystatus = json.loads(response.content)
        return_dict['myinstall-status'] = mystatus["openconfig-image-management:image-management"]["install"]["state"]["install-status"]
        return_dict['myimgstatus'] = mystatus["openconfig-image-management:image-management"]["install"]["state"]["transfer-status"]
        return_dict['percent_install'] = mystatus["openconfig-image-management:image-management"]["install"]["state"]["file-progress"]
        return_dict['myimage'] = mystatus["openconfig-image-management:image-management"]["global"]["state"]["next-boot"]
        return return_dict

def check_boot_order(remote_sw):
    """
       Check Boot Order
    """

    switch_ip = remote_sw['ip_switch']
    user_name = remote_sw['sonic_username']
    password = remote_sw['sonic_password']

    try:
       response = requests.get(url=f"https://{switch_ip}/restconf/data/openconfig-image-management:image-management/global/state",
                                headers={'Content-Type': 'application/yang-data+json'},
                                auth=HTTPBasicAuth(f"{user_name}", f"{password}"),
                                verify=False
                                )
       response.raise_for_status()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        myreturn = False
        return myreturn
    except Exception as err:
        print(f'Other error occurred: {err}')
        myreturn =  False
        return myreturn
    else:
        return_dict = dict();
        mystatus = json.loads(response.content)
        return_dict['current'] = mystatus["openconfig-image-management:state"]["current"]
        return_dict['next'] = mystatus["openconfig-image-management:state"]["next-boot"]
        return return_dict


def main():
    parser = argparse.ArgumentParser(description='Remote Firmware Upgrade tools')
    parser.add_argument("--method", help="http or https only", type=str)
    parser.add_argument("--server_ip", help="Web server IP", type=str)
    parser.add_argument("--switch_ip", help="IP address of the switch to automate", type=str)
    parser.add_argument("--filename", help="filename includding path", type=str)
    parser.add_argument("--sonic_username", help="SONiC Login", type=str)
    parser.add_argument("--sonic_password", help="SONiC Password", type=str)
    args = parser.parse_args()

    method = args.method.lower()
    filename = args.filename

    ip_switch = args.switch_ip
    server_ip = args.server_ip
    if validate_ip_address(ip_switch) == True and validate_ip_address(server_ip) == True :

     sonic_username = args.sonic_username
     sonic_password = args.sonic_password

     remote_sw = {'ip_switch':ip_switch, 'sonic_username':sonic_username, 'sonic_password':sonic_password}

     if method == "http" or "https":
       return_boot = check_boot_order(remote_sw)
       if return_boot != False:
        boot_current = return_boot['current']
        print(f'current : {boot_current}')

        result = rpcupdate(remote_sw, server_ip=server_ip, method=method, firmware=filename)
        print(f'Start Downloading : {result}')

        return_status = check_status(remote_sw)
        checkstate = return_status['myinstall-status']
        checkimage = return_status['myimage']
        checktransfert = return_status['myimgstatus']
        installPercent = return_status['percent_install']


        print (f'{checktransfert} : {installPercent}%')
        loops=0
        while checkstate == "INSTALL_IDLE":
         return_status = check_status(remote_sw)
         checkstate = return_status['myinstall-status']
         checkimage = return_status['myimage']
         checktransfert = return_status['myimgstatus']
         installPercent = return_status['percent_install']

         if checktransfert == "TRANSFER_FILE_EXTRACTION":
             print(f'Please Wait...')

         if checktransfert == "TRANSFER_FILE_VALIDATION_FAILED":
           print(f'{checktransfert}')
           result_cancel = cancel_install(remote_sw)
           result = 'FAIL'
           break

         if checktransfert == "TRANSFER_VALIDATION" and installPercent ==100:
          print(f'Check in progress {loops}')
          loops = loops+1
          if loops >200:
           result_cancel = cancel_install(remote_sw)
           result = 'FAIL'
           break

         else:
             print(f'Status: {checktransfert}')

        while checkstate == "INSTALL_PROGRESS":
         return_status = check_status(remote_sw)
         checkstate = return_status['myinstall-status']
         print(f'Please wait : {checkstate}')

        if checkstate == "INSTALL_FAILED":
           result_cancel = cancel_install(remote_sw)
           result = 'FAIL'

        if checkstate == "INSTALL_STATE_SUCCESS":
         print(f'Next step Boot Swap')
         return_status = check_status(remote_sw)
         checkimage = return_status['myimage']
         result = bootswap(remote_sw, firmware=checkimage)
         if result == "SUCCESS":
          print(f'Boot Order change: {result}')
          return_boot = check_boot_order(remote_sw)
          boot_next = return_boot['next']
          print(f'next-boot : {boot_next}')


        if result == "FAIL":
            print(f'{result} : Check CRC for {filename}, Install Cancelation {result_cancel}')


       else:
         print("IP address is not valid or unreachable\r\nUse rpc_update.py -h for Help")


if __name__ == '__main__':
    main()
