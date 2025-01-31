#!/usr/share/ucs-test/runner python3
## desc: Check the App installation if the next free port is already used
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import os
import socket

from univention.testing.utils import get_ldap_connection

from dockertest import App, Appcenter, get_app_name, get_app_version, get_docker_appbox_image, get_docker_appbox_ucs


def _open_port(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('', port))
    except OSError as msg:
        print(f'Bind failed. Error Code : {msg} {msg.errno} {os.strerror(msg.errno)}')
        return
    s.listen(10)
    print('Opened socket on port %d' % port)
    return s


if __name__ == '__main__':
    sockets = [_open_port(i) for i in range(40000, 40100)]

    with Appcenter() as appcenter:
        app_name = get_app_name()
        app_version = get_app_version()

        app = App(name=app_name, version=app_version, container_version=get_docker_appbox_ucs())

        try:
            app.set_ini_parameter(
                DockerImage=get_docker_appbox_image(),
                WebInterface='/%s' % app.app_name,
                WebInterfacePortHTTP='80',
                WebInterfacePortHTTPS='443',
                AutoModProxy='True',
                DockerScriptSetup='/usr/sbin/%s-setup' % app_name,
            )
            app.create_basic_modproxy_settings()
            app.add_to_local_appcenter()

            appcenter.update()

            app.install()

            app.verify()

            app.verify_basic_modproxy_settings()

            lo = get_ldap_connection()
            print(lo.searchDn(filter='(&(cn=%s-*)(objectClass=univentionMemberServer)(!(aRecord=*))(!(macAddress=*)))' % app_name[:5], unique=True, required=True))
        finally:
            app.uninstall()
            app.remove()

    for s in sockets:
        if not s:
            continue
        s.close()
