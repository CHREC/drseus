from django import setup
from django.conf import settings

from .arguments import get_options, parser

# TODO: log event for checkpoint merge
# TODO: log files (new table)
# TODO: add latent iteration logs to log viewer
# TODO: disable simics a9 injection into CPU: cpsr bits 2-4
# TODO: add supervisor command to load injected state (simics)
# TODO: add runtime seconds to inject command
# TODO: consider generating event filter choices only once at startup
# TODO: use regular expressions in telnet expect in jtag
# TODO: add mode to redo injection iteration
# TODO: add support for injection of multi-bit upsets


def run():
    options = get_options()
    settings.configure(
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
    missing_args = []
    campaign = None
    if options.command == 'power' and not options.power_switch_ip_address:
        options.power_switch_ip_address = '10.42.0.60'
    if options.command in ('inject', 'supervise', 'delete', 'regenerate') and \
            not (options.command == 'delete' and
                 options.selection in ('a', 'all')):
        if not options.campaign_id:
            options.campaign_id = database.get_campaign(options).id
        campaign = utilities.get_campaign(options)
        if options.command != 'regenerate':
            options.architecture = campaign.architecture
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
                if not options.aux_prompt:
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
