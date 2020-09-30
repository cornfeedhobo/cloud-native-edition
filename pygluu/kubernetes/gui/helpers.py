from pygluu.kubernetes.helpers import get_logger
logger = get_logger("gluu-gui")


def determine_ip_nodes():
    """Attempts to detect and return ip automatically.
    Also set node names, zones, and addresses in a cloud deployment.

    :return:
    """
    from pygluu.kubernetes.kubeapi import Kubernetes
    from pygluu.kubernetes.settings import SettingsHandler
    kubernetes = Kubernetes()
    settings = SettingsHandler()
    logger.info("Determining OS type and attempting to gather external IP address")
    ip = ""
    data = {}
    # detect IP address automatically (if possible)
    try:
        node_ip_list = []
        node_zone_list = []
        node_name_list = []
        node_list = kubernetes.list_nodes().items

        for node in node_list:
            node_name = node.metadata.name
            node_addresses = kubernetes.read_node(name=node_name).status.addresses
            if settings.get("DEPLOYMENT_ARCH") in ("microk8s", "minikube"):
                for add in node_addresses:
                    if add.type == "InternalIP":
                        data["ip"] = ip = add.address
                        node_ip_list.append(ip)
            else:
                for add in node_addresses:
                    if add.type == "ExternalIP":
                        data["ip"] = ip = add.address
                        node_ip_list.append(ip)
                # Digital Ocean does not provide zone support yet
                if settings.get("DEPLOYMENT_ARCH") not in ("do", "local"):
                    node_zone = node.metadata.labels["failure-domain.beta.kubernetes.io/zone"]
                    node_zone_list.append(node_zone)
                node_name_list.append(node_name)

        data["NODES_NAMES"] = node_name_list
        data["NODES_ZONES"] = node_zone_list
        data["NODES_IPS"] = node_ip_list

        if settings.get("DEPLOYMENT_ARCH") in ("eks", "gke", "do", "local", "aks"):
            #  Assign random IP. IP will be changed by either the update ip script, GKE external ip or nlb ip
            data["ip"] = "22.22.22.22"
        return data
    except Exception as e:

        logger.error(e)
        # prompt for user-inputted IP address
        logger.warning("Cannot determine IP address")
        # return a fail safe
        return {
            "ip": "127.0.0.1",
            "NODES_NAMES": [],
            "NODES_ZONES": [],
            "NODES_IPS": []
        }