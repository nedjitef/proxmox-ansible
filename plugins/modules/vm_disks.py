#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, inett GmbH <mhill@inett.de>
# GNU General Public License v3.0+
# (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Maximilian Hill'
}

DOCUMENTATION = '''
---
module: vm_disks
short_description: Configure new disks on a VM
version_added: "2.9"

description:
    - "Configure new disks on a VM"
    - "Currently only SCSI devices are supported"

options:
    vmid:
        description:
             - Id of the VM to configure
        type: int
        required: true
    scsi:
        description:
            - Config key of the device to be resized
        type: dict
        required: false
    storage:
        description:
            - Storage disk(s) should be created in
        type: int
        required: false

author:
    - Maximilian Hill <mhill@inett.de>
'''

EXAMPLES = r'''
- name: create disk
  vars:
    c_key: "scsi{{ item.key }}"
  delegate_to: "{{ pve_target_node }}"
  inett.pve.vm_disks:
    vmid: "{{ pve_vmid }}"
    scsi:
      1: {"size": 500, "ssd": true, "storage": "rbd"}
    storage: "{{ pve_vm_storage }}"
'''

RETURN = r'''
changed:
    description: Returns true if the module execution changed anything
    type: boolean
    returned: always
message:
    description: State of subscription after module execution
    type: dict
    returned: always
original_message:
    description: State of subscription after module execution
    type: dict
    returned: always
'''


from ansible_collections.inett.pve.plugins.module_utils.pve import PveApiModule


def run_module():
    arg_spec = dict(
        # state=dict(
        #     choices=['absent', 'running', 'stopped'],
        #     required=False, default='stopped'
        # ),

        # VM identification
        vmid=dict(type='int', required=False, default=None),

        # Storage configuration
        scsi=dict(
            type='dict', required=False, default={},  # elements='dict'
        ),
        # Fallback storage
        storage=dict(type='str', required=False, default=None),
    )

    mod = PveApiModule(argument_spec=arg_spec, supports_check_mode=True)
    vm, vm_config = mod.vm_config_get(mod.params['vmid'])
    update_params = dict()
    update_args = dict()

    for k, s in mod.params.get('scsi', dict()).items():
        update_args["scsi%s" % k] = s
        update_params["scsi%s" % k] = dict(
            file="%s:%d" % (
                s.get('storage', mod.params.get('storage')),
                s.get('size', 32)
            ),
            cache=s.get('cache', 'writeback'),
            discard=('on' if s.get('discard', True) else 'ignore'),
            ssd=('on' if s.get('ssd', True) else 'ignore'),
            mbps_rd=600, mbps_wr=300,
        )

    message = update_params

    old_message = dict({k: vm_config.get(k, None) for (k, v) in update_params.items()})
    changed = (old_message != message)

    if changed and not mod.check_mode:
        for k, v in update_params.items():
            if k not in vm_config.items():
                mod.vm_config_set(
                    mod.params.get('vmid'),
                    node=vm['node'],
                    config={k: v},
                    vm=vm
                )

    mod.exit_json(
        changed=changed,
        message=message,
        original_message=old_message
    )


def main():
    run_module()


if __name__ == '__main__':
    main()

