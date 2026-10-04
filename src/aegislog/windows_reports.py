"""Interpret Windows diagnostic records without treating provider names as errors."""
import re
from .parsers import WINDOWS_EVENT
from .safe_json import loads


def report_signal(line):
    match = WINDOWS_EVENT.match(line)
    if not match or match.group('provider').strip().lower() != 'windows error reporting' or match.group('event_id') != '1001':
        return None
    message = match.group('message')
    plain, marker, encoded = message.rpartition(' | AEGIS_EVENT_DATA=')
    fields = {}
    if marker:
        try:
            parsed = loads(encoded)
        except (ValueError, TypeError, RecursionError):
            pass
        else:
            if isinstance(parsed, dict):
                fields = parsed
                message = plain
    found = re.search(r'\bEvent Name:\s*([\w.-]+)', message, re.I)
    name = str(fields.get('EventName') or (found.group(1) if found else '')).casefold()
    program = str(fields.get('P1') or '')
    if not program:
        found = re.search(r'\bP1:\s*(\S+)', message)
        program = found.group(1) if found else ''
    if name == 'livekernelevent':
        return ('MEDIUM', 'service', 'Windows kernel live-dump report recorded',
                'Review the named LiveKernelReports dump and its original time, then correlate driver, graphics and hardware events. A report submission does not establish a new failure or its cause.')
    if name == 'crashpad_log' and program.casefold() == 'microsoftedgeupdate.exe':
        return ('LOW', 'service', 'Edge updater diagnostic report recorded',
                'Inspect MicrosoftEdgeUpdate.log and the reported launch/error code. Check update outcome and original event time before changing the updater or assuming a browser crash.')
    if name.startswith('apphang'):
        return ('MEDIUM', 'service', 'Windows application hang report recorded',
                'Identify the application and original hang time, then correlate its own logs and resource pressure. Repeated report submissions may describe one earlier hang.')
    if name in {'appcrash', 'bex', 'bex64', 'bluescreen'}:
        return ('MEDIUM', 'service', 'Windows fault report recorded',
                'Review the recorded application or bugcheck type and original dump/report time. Validate user impact and surrounding events; repeated submissions are not distinct confirmed failures.')
    return ('INFO', 'diagnostic', 'Windows diagnostic report recorded',
            'Review the recorded event type and original report time. The Windows Error Reporting provider name alone does not indicate an operational error or a new failure.')
