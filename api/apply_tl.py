#!/usr/bin/env python3
"""Patch an official api.tl (layer 233) with the Blue Tag additions from blue_tag.tl."""
import re, sys, pathlib
here = pathlib.Path(__file__).parent
add = [l.strip() for l in (here / 'blue_tag.tl').read_text().splitlines() if '#' in l and not l.startswith('//')]
path = pathlib.Path(sys.argv[1]); src = path.read_text().splitlines()
names = {re.match(r'([\w.]+)#', l).group(1): l for l in add}
done = set(); out = []
for l in src:
    m = re.match(r'([\w.]+)#', l)
    if m and m.group(1) in names:
        out.append(names[m.group(1)]); done.add(m.group(1))
    else:
        out.append(l)
    if l.startswith('channelAdminLogEventActionParticipantEditRank#'):
        out.append(names['channelAdminLogEventActionParticipantEditTagPerks']); done.add('channelAdminLogEventActionParticipantEditTagPerks')
    if l.startswith('chatBannedRights#'):
        out.append(names['chatMemberTagPerks']); done.add('chatMemberTagPerks')
    if l.startswith('channels.getParticipant#'):
        out.append(names['channels.editMemberTagPerks']); done.add('channels.editMemberTagPerks')
missing = set(names) - done
assert not missing, missing
path.write_text('\n'.join(out) + '\n')
print('patched', path, len(done), 'definitions')
