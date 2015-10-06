from jinja2.utils import soft_unicode

def get_subnets(value, tag_key, tag_value, return_key='id'):
    # return an attribute for all subnets that match
    subnets = []
    for item in value:
      for key, value in item['resource_tags'].iteritems():
        if key == tag_key and value == tag_value:
          subnets.append(item[return_key])

    return subnets

def get_dns_zone(value, zone_name):
    for zone in value['HostedZones']:
        if zone['Name'] == zone_name:
            return zone

class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            'get_subnets': get_subnets,
            'get_dns_zone': get_dns_zone
        }
