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


def rpcupdate(switch_ip: str, server_ip: str, method: str, firmware: str, user_name: str, password: str) -> str:
    """
        update firmware OS on SONiC OS
        Take Parmeter from the commande line
            method available:
                HTTP/S
    """

    image_name = method+"://"+server_ip+"/"+firmware
    print (image_name)

    request_data = {
        "openconfig-image-management:input": {
           "image-name": image_name
        }
    }

    #print(json.dumps(request_data))
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
        #print(f'{response}')
        mystatus = json.loads(response.content)
        myreturn = mystatus["openconfig-image-management:output"]["status-detail"]
        #return response.content
        return myreturn

def bootswap(switch_ip: str, firmware: str, user_name: str, password: str) -> str:
    """
        Swap Boot Firmware
    """

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
        #print(f'{response}')
        mystatus = json.loads(response.content)
        myreturn = mystatus["openconfig-image-management:output"]["status-detail"]
        #return response.content
        return myreturn

def check_status(switch_ip: str, user_name: str, password: str):
    """
       Check Firmware Status Upgrade
    """

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
        #print(f'{response}')
        mystatus = json.loads(response.content)
        myreturn = mystatus["openconfig-image-management:image-management"]["install"]["state"]["install-status"]
        myimage = mystatus["openconfig-image-management:image-management"]["global"]["state"]["next-boot"]
        #return response.content
        return [myreturn, myimage]


def main():
    parser = argparse.ArgumentParser(description='Remote Firmware Upgrade tools')
    parser.add_argument("--method", help="http or https only", type=str)
    parser.add_argument("--server_ip", help="Web server IP", type=str)
    parser.add_argument("--switch_ip", help="IP address of the switch to automate", type=str)
    parser.add_argument("--filename", help="filename includding path", type=str)
    parser.add_argument("--sonic_username", help="SONiC Login", type=str)
    parser.add_argument("--sonic_password", help="SONiC Password", type=str)
    args = parser.parse_args()

    method = args.method
    filename = args.filename

    switch_ip = args.switch_ip
    server_ip = args.server_ip

    if validate_ip_address(switch_ip) == True and validate_ip_address(server_ip) == True :

       sonic_username = args.sonic_username
       sonic_password = args.sonic_password

       if method == "http" or "https":
        ## result = rpcupdate(switch_ip=switch_ip, server_ip=server_ip, method=method, firmware=filename, user_name=sonic_username, password=sonic_password)
        ## print(f'{result}')
        checkstate, checkimage = check_status(switch_ip=switch_ip, user_name=sonic_username, password=sonic_password)
        print (f'{checkstate}')
        print (f'{checkimage}')
        while checkstate != "INSTALL_STATE_SUCCESS":
             checkstate = check_status(switch_ip=switch_ip, user_name=sonic_username, password=sonic_password)
             print(f'{checkstate}')
        result = "SUCCESS"
        if result == "SUCCESS" and checkstate == "INSTALL_STATE_SUCCESS":
            result = bootswap(switch_ip=switch_ip, firmware=checkimage, user_name=sonic_username, password=sonic_password)
            print(f'{result}')
    else:
      print("IP address is not valid\r\nUse rpc_update.py -h for Help")


if __name__ == '__main__':
    main()
