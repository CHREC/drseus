"""
Copyright (c) 2018 NSF Center for Space, High-performance, and Resilient Computing (SHREC)
University of Pittsburgh. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.
"""

from django import setup
from django.conf import settings

from .arguments import get_options, parser

# TODO: update to django 2
# TODO: do we need to worry about g-cache otag?
# TODO: improve execution timing in Simics
# TODO: fix rename outcome on results page filter update
# TODO: put AUX files/logs into subdirectory (in case named same as dut files)
# TODO: display AUX log files in log browser
# TODO: handle log files in simics.time_application
# TODO: check for kill aux and kill dut both specified (invalid)
# TODO: log event for checkpoint merge (including output)
# TODO: add latent iteration logs to log viewer
# TODO: disable simics a9 injection into CPU: cpsr bits 2-4
# TODO: add supervisor command to load injected state (simics)
# TODO: add runtime seconds to inject command
# TODO: use regular expressions in telnet expect in jtag
# TODO: add mode to redo injection iteration
# TODO: add support for injection of multi-bit upsets
# TODO: add documentation on system design, including module interaction


def run():
    options = get_options()
    settings.configure(
        ALLOWED_HOSTS=['*'],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': options.db_name,
                'USER': options.db_user,
                'PASSWORD': options.db_password,
                'HOST': options.db_host,
                'PORT': options.db_port,
            } if options.db_postgresql else {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': options.db_file
            }
        },
        DEBUG=True,
        INSTALLED_APPS=(
            'django.contrib.staticfiles',
            'django_filters',
            'django_tables2',
            '{}.log'.format(__name__)
        ),
        ROOT_URLCONF='{}.log.urls'.format(__name__),
        STATIC_URL='/static/',
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.request',
                    ],
                },
            },
        ],
        TIME_ZONE='UTC'
    )
    setup()
    # we can't (indirectly) import anything from log until django is setup
    from . import database
    from . import utilities
    from .jtag import find_devices
    missing_args = []
    campaign = None
    if options.command in (
            'inject', 'supervise', 'delete', 'regenerate', 'hashes'
            ) and not (options.command == 'delete' and
                       options.selection in ('a', 'all')):
        campaign = database.get_campaign(options)
        if not options.campaign_id:
            options.campaign_id = campaign.id
            if not options.command == 'delete' and input(
                    'no campaign was specified, continue with campaign id {}?'
                    ' [Y/n]: '.format(options.campaign_id)) not in \
                    ['y', 'Y', 'yes', 'Yes', 'YES', '']:
                return
        if options.command != 'regenerate':
            options.architecture = campaign.architecture
    uarts = find_devices()['uart']
    if not options.dut_serial_port and options.dut_dev_serial:
        for uart in uarts:
            if 'serial' in uarts[uart] and \
                    options.dut_dev_serial == uarts[uart]['serial']:
                options.dut_serial_port = uart
                if uarts[uart]['type'] == 'pynq':
                    options.dut_rtscts = False
    if not options.aux_serial_port and options.aux_dev_serial:
        for uart in uarts:
            if 'serial' in uarts[uart] and \
                    options.aux_dev_serial == uarts[uart]['serial']:
                options.aux_serial_port = uart
                if uarts[uart]['type'] == 'pynq':
                    options.aux_rtscts = False
    if options.command in ('new', 'inject', 'supervise'):
        if (hasattr(options, 'simics') and not options.simics) or \
                (campaign and not campaign.simics):
            # not using simics
            if not options.dut_serial_port:
                missing_args.append('--serial')
            if not options.dut_prompt:
                missing_args.append('--prompt')
            if (hasattr(options, 'aux') and options.aux) or \
                    (campaign and campaign.aux):
                if not options.aux_serial_port:
                    missing_args.append('--aux_serial')
                if not options.aux_readonly and not options.aux_prompt:
                    missing_args.append('--aux_prompt')
            if not options.debugger_ip_address and (
                    (hasattr(options, 'architecture') and
                        options.architecture == 'p2020') or
                    (campaign and campaign.architecture == 'p2020')):
                # using p2020 (not using simics)
                missing_args.append('--jtag_ip')
        if options.command == 'supervise' and not campaign.simics and \
                options.power_switch_outlet is not None:
            missing_args.append('--power_ip')
    if options.command == 'minicom' and not options.dut_serial_port:
        missing_args.append('--serial')
    if missing_args:
        parser.print_usage()
        print('error: the following arguments are required: {}'.format(
            ', '.join(missing_args)))
        if '--serial' in missing_args or '--aux_serial' in missing_args:
            print('\nAvailable serial devices:')
            utilities.list_devices(only_uart=True)
        return
    getattr(utilities, options.func)(options)
