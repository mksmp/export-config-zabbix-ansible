from pyzabbix import ZabbixAPI
import argparse


# Auth Zabbix API to export
def zabbix_auth_from(host_from):
    zapi = ZabbixAPI("http://" + host_from)
    zapi.login("Admin", "zabbix")
    print("Connected to Zabbix API Version %s" % zapi.api_version())
    return zapi


# Auth Zabbix API to import
def zabbix_auth_to(url_link):
    zapi = ZabbixAPI('http://' + url_link + ':8080')
    zapi.login("Admin", "zabbix")
    print("Connected to Zabbix API Version %s" % zapi.api_version())
    return zapi


# ARGS
def set_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        # "-h ",
        "--host_to",
        dest="host_to",
        help="HOST TO COPY URL"
    )
    parser.add_argument(
        # "-h ",
        "--host_from",
        dest="host_from",
        help="HOST FROM COPY URL"
    )
    args = parser.parse_args()

    return args


# Func for make export files
def write_export(name, config, export_format):
    if config is not None:
        print("Writing %s.%s" % (name, export_format))
        with open("%s.%s" % (name, export_format), "w") as f:
            f.write(config)


# Func for export hosts from main zabbix
def export_hosts(zapi, namefile = "export_zabbix_hosts"):
    hosts_ids = []
    for item in zapi.host.get(output="extend"):
        hosts_ids.append(int(item['hostid']))

    config = zapi.configuration.export(
        format="yaml", prettyprint=True, options={"hosts": hosts_ids}
    )
    write_export(namefile, config, "yml")


# Func for export templates from main zabbix
def export_templates(zapi, namefile = "export_zabbix_templates"):
    hosts_ids = []
    for item in zapi.template.get(output="extend"):
        hosts_ids.append(int(item['templateid']))

    config = zapi.configuration.export(
        format="yaml", prettyprint=True, options={"templates": hosts_ids}
    )
    write_export(namefile, config, "yml")


# Func for export host groups from main zabbix
def export_host_groups(zapi, namefile = "export_zabbix_hostgroups"):
    hosts_groups_ids = []
    for item in zapi.hostgroup.get(output="extend"):
        hosts_groups_ids.append(int(item["groupid"]))

    config = zapi.configuration.export(
        format="yaml", prettyprint=True, options={"groups": hosts_groups_ids}
    )
    write_export(namefile, config, "yml")


# Func for import config to copy of zabbix
def import_config(zapi, filename, rules):
    print("Import " + filename.split('_')[-1].split('.')[0])
    export_file = open(filename, "r").read()
    zapi.configuration['import'](format="yaml", source=export_file, rules=rules)


def export_zabbix_conf(zapi):
    export_templates(zapi)
    export_hosts(zapi)
    export_host_groups(zapi)


def import_zabbix_conf(zapi):
    import_config(zapi, "export_zabbix_templates.yml", { "templates": { "createMissing": True, "updateExisting": True }})
    import_config(zapi, "export_zabbix_hostgroups.yml", { "host_groups": {"createMissing": True }})
    import_config(zapi, "export_zabbix_hosts.yml", {"hosts": { "createMissing": True, "updateExisting": True }})


# Func for rename localhost on zabbix-server, for find it by zabbix-agent2
def rename_local_host(zapi, remote_host):
    try:
        hid=zapi.host.get(search={'host': remote_host})[0]['hostid']
    except:
        hid=zapi.host.get(search={'host': 'Zabbix server'})[0]['hostid']
    print('Change name')
    zapi.host.update(hostid=hid, host=remote_host, name=remote_host)
    print('Change DNS name')
    iid = zapi.hostinterface.get(hostids=hid)[0]['interfaceid']
    zapi.hostinterface.update(interfaceid=iid, dns=remote_host, useip=0, ip='172.127.0.6')  


if __name__ == "__main__":
    args = set_arguments()
    zapi_from = zabbix_auth_from(args.host_from)
    zapi_to = zabbix_auth_to(args.host_to)
    export_zabbix_conf(zapi_from)
    import_zabbix_conf(zapi_to)
    rename_local_host(zapi_to, args.host_to)
