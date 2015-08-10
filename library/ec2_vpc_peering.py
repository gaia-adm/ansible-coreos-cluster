#!/usr/bin/env python
"""
Ansible module to manage VPC peering connections
"""

DOCUMENTATION = '''
---
module: ec2_vpc_peering
short_description: manage AWS VPC Peering Connections
description:
    - Create, list or reject/delete AWS VPC peering connections.
    - This module has a dependency on python-boto
version_added: "1.7.2"
author: Herby Gillot <herby.gillot@gmail.com>
notes:
    - You can specify VPCs via their VPC ID, CIDR block or tagged name.  If you use a CIDR or name and it matches more than one VPC, the module will abort, at which point you'd need to use something more specific (like the VPC's ID).
    - This module uses the account ID of the current AWS API user to determine whether or not it can or cannot accept a peering connection that is pending acceptance.  The 'force' flag can be used skip this check, and will attempt acceptance of every pending-acceptance connection seen, no matter what the accepting account ID is.
options:
    name:
        description:
            - Name to tag this connection with
        required: false
        default: null
    source_vpc:
        description:
            - VPC ID, CIDR block or name tag of the requesting VPC
            - Required for all states except "list"
        required: false
        default: null
    peer_vpc:
        description:
            - VPC ID, CIDR block or name tag of the accepting VPC
            - Required for all states except "list"
        required: false
        default: null
        aliases: ['dest_vpc']
    peer_owner_id:
        description:
            - Account ID of the owner of the accepting VPC, if different.
        required: false
        default: null
    state:
        description:
            - Sets desired state for this VPC peering connection. If set to 'pending', if the connection does not exist, it will be created in the 'pending-acceptance' state. If set to 'present' or 'active', and both the source and dest VPC are owned by you, this module will create and set the connection to be active.
        required: false
        default: 'present'
        choices: ['absent', 'present', 'active', 'pending', 'list']
    force_accept:
        description:
            - Normally, this module only accepts pending connections that it owns.
            - Enabling this option attempts to accept all connections seens that are pending acceptance.
        required: false
        default: false
    ignore_rejection:
        description:
            - By default, this module does not attempt to re-create a connection that has been rejected.
            - Enabling this option will create connections even if they have been rejected.
        required: false
        default: false
    always_delete:
        description:
            - By default, when removing connections, connections in a pending-acceptance state will be rejected.
            - Enabling this flag will always delete a connection whether it is pending acceptance or not.
        required: false
        default: false

extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Create a VPC peering connection between ovpc1 and ovpc2
- local_action: 
    module: ec2_vpc_peering
    name: 'ovpc1-to-ovpc2'
    source_vpc: 'ovpc1'
    dest_vpc: 'ovpc2'
    region: 'us-west-1'
    state: 'present'
    
# List all VPC peering connections
- local_action:
    module: ec2_vpc_peering
    region: 'us-east-1'
    state:  'list'
  register: peering_list

- debug: var=peering_list

# Create a VPC peering connection from your VPC with CIDR 10.0.0.0/16 
# to vpc ID vpc-01234567, owned by the account ID 012345678901
- local_action: 
    module: ec2_vpc_peering
    source_vpc: '10.0.0.0/16'
    dest_vpc: 'vpc-01234567'
    peer_owner_id: '012345678901'
    region: 'us-east-1'
    state: 'present'

# Ensure any peering connections between the VPCs with the CIDRS 10.10.1.0/24
# and 10.10.2.0/24 are not present.
- local_action: 
  module: ec2_vpc_peering
  source_vpc: '10.10.1.0/24'
  dest_vpc: '10.10.2.0/24'
  region: 'us-west-1'
  state: 'absent'
'''

from boto.exception import EC2ResponseError
from operator import attrgetter, itemgetter

import boto.iam
import boto.vpc
import re
import time


CIDR_RE = re.compile('^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$')


def is_cidr_format(strng):
    """
    Returns True or False depending on whether the given string looks like
    a CIDR block specification.
    """
    return bool(re.match(CIDR_RE, strng))


class AWSAccountUtil(object):
    """
    Simple AWS account utility
    """
    def __init__(self, region, **boto_params):
        self.conn = boto.iam.connect_to_region(region, **boto_params)

    def get_account_id(self):
        return self.conn.get_user().user.arn.split(':')[4]


class VPCPeeringUtil(object):

    VALID_CONNECTION_STATES = (
        'active',
        'initiating-request',
        'pending-acceptance',
        'provisioning',
    )

    INVALID_CONNECTION_STATES = (
        'rejected',
        'failed',
        'deleted'
    )

    CONNECTION_STATES = \
        VALID_CONNECTION_STATES + \
        INVALID_CONNECTION_STATES

    def __init__(self, region, check_mode=False, **boto_params):
        self.conn = boto.vpc.connect_to_region(region, **boto_params)
        self.acct = AWSAccountUtil(region, **boto_params)
        self.dry_run_mode = check_mode

    def is_owned_by_this_user(self, connection):
        """
        Given a peering connection object, return True if it looks as if this
        peering connection is entirely owned by this user.
        """
        current_acct_id = self.acct.get_account_id()
        return (connection.accepter_vpc_info.owner_id == current_acct_id)

    def is_pending_accept(self, connection):
        return connection and (connection.status_code == 'pending-acceptance')

    def is_valid_connection(self, connection):
        return connection and \
            (connection.status_code in self.VALID_CONNECTION_STATES)

    def accept_peering_connection(self, connection_id):
        """
        Given a connection ID, attempt to accept the peering request
        """
        return self.conn.accept_vpc_peering_connection(
            connection_id, dry_run=self.dry_run_mode)

    def create_peering_connection_by_identifier(
            self, source, peer, connection_name=None, peer_owner_id=None):
        """
        Given a source and peer VPC name, CIDR or ID (and optional peer owner
        ID), create a new peering connection between the 2 VPCs.
        """
        source = self.find_required_vpc(source).id

        if not peer_owner_id:
            peer = self.find_required_vpc(peer).id

        connection = self.conn.create_vpc_peering_connection(
            source, peer, peer_owner_id, dry_run=self.dry_run_mode)

        if connection_name:
            connection.add_tag('Name', connection_name)

        return connection

    def delete_peering_connection(self, connection_id):
        """
        Given a VPC peering connection ID, delete it.
        """
        return self.conn.delete_vpc_peering_connection(
            connection_id, dry_run=self.dry_run_mode)
       
    def find_required_vpc(self, identifier, state='available'):
        """
        Attempts to find a single VPC for the given identifier.

        Raises an exception if none or too many are found.
        """
        vpc = self.find_vpc(identifier, raise_on_many=True)

        if not vpc:
            raise ValueError(
                'No VPC found for identifier "{}"'.format(identifier))
        return vpc

    def find_vpc(self, identifier, state='available', raise_on_many=False):
        """
        Given an identifier, searches for a single VPC matching that identifier

        Tries searching with the identifier as:

        1) VPC ID,
        2) CIDR block (if applicable)
        3) Name tag

        Returns None if a single VPC could not be found doing any of the above.

        'state' can be specified as 'pending' if searching not-yet-available
        VPCs is desired.

        If 'raise_on_many' is set to True, raises ValueError if ever more than
        one VPC is found for the given identifier.
        """
        vpcs = list()

        base_filters = {'state': state}
        as_name = {'tag:Name': identifier}
        as_cidr = {'cidr': identifier}
        map(lambda d: d.update(base_filters), (as_name, as_cidr))

        vpcs = self.get_all_vpcs(vpc_ids=[identifier], filters=base_filters)

        if len(vpcs) == 1:
            return vpcs[0]
        elif len(vpcs) > 1 and raise_on_many:
            raise ValueError(
                'More than one VPC found for "{}"'.format(identifier))

        if is_cidr_format(identifier):
            vpcs = self.get_all_vpcs(filters=as_cidr)

            if len(vpcs) == 1:
                return vpcs[0]
            elif len(vpcs) > 1 and raise_on_many:
                raise ValueError(
                    'More than one VPC found for "{}"'.format(identifier))

        vpcs = self.get_all_vpcs(filters=as_name)

        if len(vpcs) == 1:
            return vpcs[0]
        elif len(vpcs) > 1 and raise_on_many:
            raise ValueError(
                'More than one VPC found for "{}"'.format(identifier))
        return None

    def get_all_vpcs(self, **params):
        """
        Return list of VPCs as per parameters, empty list if none found.
        """
        vpcs = list()
        try:
            vpcs = self.conn.get_all_vpcs(**params)
        except EC2ResponseError, e:
            if e.errors[0][0].lower() == 'invalidvpcid.notfound':
                pass
        return vpcs

    def find_matching_peering_connections(
            self, source, peer, name=None, peer_owner_id=None):
        """
        Returns a list of all VPC peering connections that match the given
        parameters.
        """

        _src = self.find_vpc(source)
        if _src:
            source = _src.id

        if not peer_owner_id:
            _peer = self.find_vpc(peer)
            if _peer:
                peer = _peer.id

        return self.find_peering_connections(source, peer, name=name,
            peer_owner_id=peer_owner_id)
        
    def find_peering_connections(
            self, source_vpc_id, peer_vpc_id, name=None, peer_owner_id=None):
        """
        Get the list of peering connections for the provided source and peer
        vpc IDs.
        """
        filters = dict()

        filters['requester-vpc-info.vpc-id'] = source_vpc_id
        filters['accepter-vpc-info.vpc-id'] = peer_vpc_id

        if peer_owner_id:
            filters['accepter-vpc-info.owner-id'] = peer_owner_id

        if name:
            filters['tag:Name'] = name

        return self.conn.get_all_vpc_peering_connections(filters=filters)

    def get_peering_connection_by_id(self, connection_id):
        """
        Get the VPC peering connection for the given peering connection ID.
        """
        results = self.conn.get_all_vpc_peering_connections(
            vpc_peering_connection_ids=[connection_id])
        if results:
            return results[0]
        else:
            return None

    def get_all_peering_connections(self):
        """
        Get all VPC peering connections.
        """
        return self.conn.get_all_vpc_peering_connections()

    def reject_peering_connection(self, connection_id):
        """
        Given a VPC peering connection ID, reject it.
        """
        return self.conn.reject_vpc_peering_connection(connection_id)

    def wait_for_connection_state(self, connection_id,
            desired_states=('pending-acceptance', 'active')):
        """
        Given a connection ID, wait until it is in a "good" state: 
        ('pending-acceptance' or 'active')
        """
        def check():
            conn = self.get_peering_connection_by_id(connection_id)
            return conn.status_code in desired_states
        wait_until_condition(check)


class VPCPeeringModule(object):

    def __init__(self, module, boto_params={}):
        for param in module.params.keys():
            setattr(self, param, module.params.get(param))

        region, ec2_url, boto_params = get_aws_connection_info(module)
        self.util = VPCPeeringUtil(region, module.check_mode, **boto_params)

    def attempt_auto_accept(self, connection):
        """
        Try to accept a peering connection in "pending-acceptance" mode if it
        looks like we can.
        """
        force = self.force_accept
        changed = False
        if self.util.is_pending_accept(connection):
            if force or self.util.is_owned_by_this_user(connection):
                self.util.accept_peering_connection(connection.id)
                changed = True
        return (changed, connection)

    def create(self):
        """
        Create a peering connection per our module parameters.
        """
        connection = self.util.create_peering_connection_by_identifier(
            self.source_vpc, self.peer_vpc, peer_owner_id=self.peer_owner_id,
            connection_name=self.name)
        self.util.wait_for_connection_state(connection.id)
        connection = self.util.get_peering_connection_by_id(connection.id)
        return connection

    def find_matching_connections(self):
        """
        Gather connections that match our specified parameters.
        """
        return self.util.find_matching_peering_connections(
            self.source_vpc, self.peer_vpc, self.peer_owner_id)

    def find_valid_matching_connections(self):
        connections = self.find_matching_connections()
        return filter(self.util.is_valid_connection, connections)

    def ensure_present(self, want_active=False):
        """
        Ensure that there are peering connections present matching
        the specified module criteria, create one if there aren't any.
        """
        changed = False
        results = list()

        connections = self.find_matching_connections()

        if not connections:
            # if no connetions at all match our criteria, create one.
            self.create()
            changed = True

        valid_connections = self.find_valid_matching_connections()

        if not valid_connections:
            # Everything is either failed, rejected or deleted.

            should_create = False

            # Don't attempt to create another peering connection if all
            # the peering connections we've seen have been rejected,
            # except in the case where we are ignoring rejections.
            if self.ignore_rejection:
                should_create = True
            else:
                get_status = attrgetter('status_code')
                all_status = list(set(map(get_status, connections)))

                if all_status != ['rejected']:
                    should_create = True

            if should_create:
                self.create()
                changed = True

        valid_connections = self.find_valid_matching_connections()

        if valid_connections:
            # if any of the existing connections per our criteria are
            # valid, and we're not wanting to force anything to be active,
            # then we won't do anything.
            if not want_active:
                return (changed, valid_connections)

            # Find all connections that are pending acceptance, and accept
            # them if it looks like that's something that we can do.
            pending = filter(
                self.util.is_pending_accept, valid_connections)
            accept_attempted = map(self.attempt_auto_accept, pending)

            changed = results_list_has_changed(accept_attempted)

        results = self.find_valid_matching_connections()
        return (changed, results)

    def ensure_absent(self):
        """
        Ensure no connections are present as per module criteria,
        delete them if there are any.
        """
        changed = False
        results = list()

        valid_connections = self.find_valid_matching_connections()

        if not valid_connections:
            return (changed, results)

        else:
            for connection in valid_connections:
                if self.always_delete or \
                        not self.util.is_pending_accept(connection):
                    self.util.delete_peering_connection(connection.id)
                else:
                    self.util.reject_peering_connection(connection.id)
            changed = True

        results = self.find_matching_connections()
        return (changed, results)

    def list_all(self):
        """
        Return the list of all VPC peering connections.
        """
        all_connections = self.util.get_all_peering_connections()
        return (False, all_connections)


def connection_as_dict(connection):
    """
    Return a peering connection as dictionary.
    """
    if not connection:
        return dict()

    return {
        'id': connection.id,
        'expiration': connection.expiration_time or '',
        'source_vpc_id':  connection.requester_vpc_info.vpc_id,
        'source_vpc_cidr': connection.requester_vpc_info.cidr_block,
        'peer_vpc_id': connection.accepter_vpc_info.vpc_id,
        'peer_vpc_cidr': connection.accepter_vpc_info.cidr_block,
        'status': connection.status_code,
        'status_message': connection.status_message,
        'tags': connection.tags
    }


def results_list_has_changed(results):
    """
    Given a list of results where each result is a tuple of the form
    (changed, ...), [where changed is a boolean], return True if this group
    has changed.
    """
    get_changed = itemgetter(0)
    return any(filter(get_changed, results))


def wait_until_condition(condition_check, interval=1):
    """
    Given a condition check as callable, sleep until the condition check
    returns True
    """
    while True:
        time.sleep(interval)
        if condition_check():
            break

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            region = dict(required=True),
            name = dict(required=False),
            source_vpc = dict(required=False),
            peer_vpc = dict(required=False, aliases=['dest_vpc']),
            peer_owner_id = dict(required=False),
            state = dict(
                choices=['absent', 'present', 'active', 'pending', 'list'],
                default='present',
                required=False),
            force_accept = dict(required=False, type='bool', default=False),
            ignore_rejection = dict(
                required=False, type='bool', default=False),
            always_delete = dict(required=False, type='bool', default=False)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
        supports_check_mode=True)

    region, ec2_url, boto_params = get_aws_connection_info(module)
    desired_state = module.params.get('state')

    vpcpmod = VPCPeeringModule(module, boto_params) 

    # source_vpc and peer_vpc are only not required when state is 'list'
    if (desired_state != 'list') and \
            ((not module.params.get('source_vpc')) or \
             (not module.params.get('peer_vpc'))):
        module.fail_json(
            msg='source_vpc and dest_vpc required unless state="list"')

    if desired_state in ('list',):
        action = lambda: vpcpmod.list_all()
    elif desired_state in ('present', 'active'):
        action = lambda: vpcpmod.ensure_present(want_active=True)
    elif desired_state in ('pending',):
        action = lambda: vpcpmod.ensure_present()
    elif desired_state in ('absent',):
        action = lambda: vpcpmod.ensure_absent()

    try:
        results = action()
    except ValueError, e:
        module.fail_json(msg=e.message)

    changed = results[0]
    items = map(connection_as_dict, results[1])

    module.exit_json(changed=changed, results=items)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
