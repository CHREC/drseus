from .arguments import get_options, parser
from . import utilities

# TODO: add runtime seconds to inject command
# TODO: consider generating event filter choices only once at startup
# TODO: update chart colors
# TODO: only send files if needed
# TODO: use regular expressions in telnet expect in jtag
# TODO: use formatting strings
# TODO: add mode to redo injection iteration
# TODO: add support for injection of multi-bit upsets


def run():
    options = get_options()
    missing_args = []
    campaign = None
    if options.command == 'power' and not options.power_switch_ip_address:
        options.power_switch_ip_address = '10.42.0.60'
    if options.command in ('inject', 'supervise', 'delete', 'regenerate') and \
            not (options.command == 'delete' and
                 options.delete in ('a', 'all')):
        if not options.campaign_id:
            campaign = utilities.get_campaign(options)
            options.campaign_id = campaign['id']
        else:
            campaign = utilities.get_campaign(options)
        if options.command != 'regenerate':
            options.architecture = campaign['architecture']
    if options.command in ('new', 'inject', 'supervise'):
        if (hasattr(options, 'simics') and not options.simics) or \
                (campaign and not campaign['simics']):
            # not using simics
            if not options.dut_serial_port:
                missing_args.append('--serial')
            if not options.dut_prompt:
                missing_args.append('--prompt')
            if not options.debugger_ip_address and (
                    (hasattr(options, 'architecture') and
                        options.architecture == 'p2020') or
                    (campaign and campaign['architecture'] == 'p2020')):
                # using p2020 (not using simics)
                missing_args.append('--jtag_ip')
        if options.command == 'supervise' and not campaign['simics'] and \
                options.power_switch_outlet is not None:
            missing_args.append('--power_ip')
    if missing_args:
        parser.error('the following arguments are required: {}'.format(
            ', '.join(missing_args)))
    getattr(utilities, options.func)(options)
