<?php
@%@UCRWARNING=# @%@

$config = array(


    // This is a authentication source which handles admin authentication.
    'admin' => array(
        // The default is to use core:AdminPassword, but it can be replaced with
        // any authentication source.

        'core:AdminPassword',
    ),
@!@
from univention.saml.lib import php_string

ucr = configRegistry
base = ucr.get("ldap/base")
hostname = ucr.get("hostname")
domain = ucr.get("domainname")
ssp_fqdn = ucr.get("ucs/server/sso/fqdn", "ucs-sso.%s" % domain)
kc_fqdn = ucr.get("keycloak/server/sso/fqdn", "ucs-sso-ng.%s" % domain)
password = ""
try:
    with open("/etc/idp-ldap-user.secret") as fd:
        password = fd.read().strip()
except EnvironmentError:
    import sys

    sys.stderr.write("/etc/idp-ldap-user.secret could not be read!\n")

print(
    """
    // An authentication source which can authenticate against both SAML 2.0
    // and Shibboleth 1.3 IdPs.
    'default-sp' => array(
        'saml:SP',

        // The entity ID of this SP.
        // Can be NULL/unset, in which case an entity ID is generated based on the metadata URL.
        'entityID' => %s,

        // The entity ID of the IdP this should SP should contact.
        // Can be NULL/unset, in which case the user will be shown a list of available IdPs.
        'idp' => %s,

        // The URL to the discovery service.
        // Can be NULL/unset, in which case a builtin discovery service will be used.
        'discoURL' => %s,

        'authproc' => array(
            50 => array(
                'class' => 'ldap:AttributeAddFromLDAP',
                'ldap.hostname' => %s,
                'ldap.username' => %s,
                'ldap.password' => %s,
                'ldap.basedn' => %s,
                'ldap.enable_tls' => TRUE,
                'attributes' => array(
                    'mailPrimaryAddress', 'memberOf', 'enabledServiceProviderIdentifier',
                    'shadowExpire', 'sambaPwdLastSet', 'shadowLastChange',
                    'shadowMax', 'sambaKickoffTime', 'krb5ValidEnd', 'krb5PasswordEnd',
                    'sambaAcctFlags', 'univentionRegisteredThroughSelfService',
                    'univentionPasswordRecoveryEmailVerified'
                ),
                'search.filter' => '(&(objectClass=person)(uid=%%uid%%))',
            ),
        ),
    ),
"""
    % (
        php_string(
            "https://%s/simplesamlphp/module.php/saml/sp/metadata.php/default-sp"
            % ssp_fqdn,
        ),
        php_string("https://%s/realms/ucs" % kc_fqdn),
        php_string("https://%s/realms/ucs/protocol/saml/descriptor" % kc_fqdn),
        php_string("ldap://%s.%s:7389" % (hostname, domain)),
        php_string("uid=sys-idp-user,cn=users,%s" % base),
        php_string(password),
        php_string(base),
    ),
)
@!@
    // LDAP authentication source.
    'univention-ldap' => array(
        'uldap:uLDAP',

        // Give the user an option to save their username for future login attempts
        // And when enabled, what should the default be, to save the username or not
        //'remember.username.enabled' => FALSE,
        //'remember.username.checked' => FALSE,

        // The hostname of the LDAP server.
        //'hostname' => '127.0.0.1',
        // Whether SSL/TLS should be used when contacting the LDAP server.
        //'enable_tls' => FALSE,


@!@
import re
from univention.lib.misc import getLDAPURIs
from univention.saml.lib import php_array, php_string

hostname = getLDAPURIs()

expiry_attributes = ['shadowExpire', 'sambaPwdLastSet', 'shadowLastChange', 'shadowMax', 'sambaKickoffTime', 'krb5ValidEnd', 'krb5PasswordEnd', 'sambaAcctFlags', 'univentionRegisteredThroughSelfService', 'univentionPasswordRecoveryEmailVerified']

config_attributes = ", ".join(filter(None, re.split('[ ,\'"]', configRegistry.get('saml/idp/ldap/get_attributes', 'uid')))).split(', ')
search_attributes = ", ".join(filter(None, re.split('[ ,\'"]', configRegistry.get('saml/idp/ldap/search_attributes', 'uid')))).split(', ')

attributes = list(set(config_attributes + expiry_attributes))


print("	'hostname'		=> %s," % php_string(hostname))
print("	'enable_tls'		=> %s," % ('TRUE' if configRegistry.is_true('saml/idp/ldap/enable_tls', True) else 'FALSE'))
print("	'debug' 		=> %s," % ('TRUE' if configRegistry.is_true('saml/idp/ldap/debug', False) else 'FALSE'))
print("	'attributes'		=> %s," % php_array(attributes))
print("	'search.base'		=> %s," % php_string(configRegistry.get('ldap/base', 'null')))
print("	'search.attributes' 	=> %s," % (php_array(search_attributes)))
print("	'search.filter' 	=> '(objectClass=person)',")
print("	'selfservice.check_email_verification' 	=> %s," % ('TRUE' if configRegistry.is_true('saml/idp/selfservice/check_email_verification', False) else 'FALSE'))

ldap_user = 'uid=sys-idp-user,cn=users,%s' % configRegistry.get('ldap/base', 'null')
if configRegistry.get('saml/idp/ldap/user'):
    ldap_user = configRegistry.get('saml/idp/ldap/user')

print("	'search.username'	=> %s," % php_string(ldap_user))

password = ''
try:
    with open('/etc/idp-ldap-user.secret') as fd:
        password = fd.read().strip()
except EnvironmentError:
    import sys
    sys.stderr.write('/etc/idp-ldap-user.secret could not be read!\n')

print("	'search.password'	=> %s," % php_string(password))
@!@


        // Whether debug output from the LDAP library should be enabled.
        // Default is FALSE.
        // 'debug' => FALSE
        // The timeout for accessing the LDAP server, in seconds.
        // The default is 0, which means no timeout.
        'timeout' => 0,

        // Set whether to follow referrals. AD Controllers may require FALSE to function.
        'referrals' => TRUE,

        // Which attributes should be retrieved from the LDAP server.
        // This can be an array of attribute names, or NULL, in which case
        // all attributes are fetched.
        //'attributes' => NULL,

        // The pattern which should be used to create the users DN given the username.
        // %username% in this pattern will be replaced with the users username.
        //
        // This option is not used if the search.enable option is set to TRUE.
        //'dnpattern' => 'uid=%username%,ou=people,dc=example,dc=org',
        //'dnpattern' => 'uid=%username%,cn=users,dc=intra,dc=example',
        // As an alternative to specifying a pattern for the users DN, it is possible to
        // search for the username in a set of attributes. This is enabled by this option.
        'search.enable' => TRUE,

        // The DN which will be used as a base for the search.
        // This can be a single string, in which case only that DN is searched, or an
        // array of strings, in which case they will be searched in the order given.
        //'search.base' => 'cn=users,dc=intra,dc=example',
        // The attribute(s) the username should match against.
        //
        // This is an array with one or more attribute names. Any of the attributes in
        // the array may match the value the username.

        // The username & password the simpleSAMLphp should bind to before searching. If
        // this is left as NULL, no bind will be performed before searching.

        // If the directory uses privilege separation,
        // the authenticated user may not be able to retrieve
        // all required attributes, a privileged entity is required
        // to get them. This is enabled with this option.
        'priv.read' => FALSE,

        // The DN & password the simpleSAMLphp should bind to before
        // retrieving attributes. These options are required if
        // 'priv.read' is set to TRUE.
        'priv.username' => NULL,
        'priv.password' => NULL,

    ),

);
