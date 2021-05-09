from consul import Consul, Check
import socket

CONSUL_PORT = 8500
SERVICE_NAME = 'invoices'
SERVICE_PORT = 5007

def get_host_name_IP(): 

    host_name_ip = ""
    try: 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host_name_ip = s.getsockname()[0]
        s.close()
        # print ("Host ip:", host_name_ip)
        return host_name_ip
    except: 
        print("Unable to get Hostname") 


def register_to_consul():
    consul = Consul(host="consul", port=CONSUL_PORT)

    agent = consul.agent

    service = agent.service

    ip = get_host_name_IP()
    # print(ip)

    check = Check.http(f"http://{ip}:{SERVICE_PORT}/api/ui", interval="10s", timeout="5s", deregister="1s")

    service.register(name = SERVICE_NAME, service_id = SERVICE_NAME, address = ip, port=SERVICE_PORT, check=check)


def get_consul_service(service_id):
    consul = Consul(host="consul", port=CONSUL_PORT)

    agent = consul.agent

    service_list = agent.services()

    service_info = service_list[service_id]

    return service_info['Address'], service_info['Port']
