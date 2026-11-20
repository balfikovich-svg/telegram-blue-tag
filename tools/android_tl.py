#!/usr/bin/env python3
"""Blue Tag: patch Telegram Android's TLRPC.java with the TL additions from api/blue_tag.tl."""
import re, sys
p = sys.argv[1]; s = open(p).read()

def cls_span(name, base):
    start = s.index(f'    public static class {name} extends {base} {{')
    end = s.index('\n    public static ', start + 10)
    return start, end

def in_class(name, base, old, new, count=1):
    global s
    a, b = cls_span(name, base); body = s[a:b]
    assert body.count(old) == count, (name, old, body.count(old))
    s = s[:a] + body.replace(old, new) + s[b:]

def once(old, new):
    global s
    assert s.count(old) == 1, (old, s.count(old)); s = s.replace(old, new)

# --- base classes
once('    public static abstract class ChannelParticipant extends TLObject {\n',
     '    public static abstract class ChannelParticipant extends TLObject {\n        public TL_chatMemberTagPerks tag_perks; // Blue Tag\n')
once('    public static abstract class Chat extends TLObject {\n',
     '    public static abstract class Chat extends TLObject {\n        public TL_chatMemberTagPerks tag_perks; // Blue Tag: my perks in this chat\n')
a = s.index('    public static class Message extends TLObject {')
i = s.index('        public String from_rank;\n', a)
s = s[:i] + '        public String from_rank;\n        public boolean from_rank_blue; // Blue Tag\n' + s[i + len('        public String from_rank;\n'):]

# --- channel
in_class('TL_channel', 'Chat', 'constructor = 0x7ad15240;', 'constructor = 0x6506067c; // Blue Tag (was 0x7ad15240)')
in_class('TL_channel', 'Chat',
    '            if (hasFlag(flags2, FLAG_22)) {\n                pinned_msg_id = stream.readInt32(exception);\n            }\n',
    '            if (hasFlag(flags2, FLAG_22)) {\n                pinned_msg_id = stream.readInt32(exception);\n            }\n'
    '            if (hasFlag(flags2, FLAG_24)) {\n                tag_perks = TL_chatMemberTagPerks.TLdeserialize(stream, stream.readInt32(exception), exception);\n            }\n')
in_class('TL_channel', 'Chat',
    '            flags2 = setFlag(flags2, FLAG_23, forum_sidebar);\n',
    '            flags2 = setFlag(flags2, FLAG_23, forum_sidebar);\n            flags2 = setFlag(flags2, FLAG_24, tag_perks != null);\n')
in_class('TL_channel', 'Chat',
    '            if (hasFlag(flags2, FLAG_22)) {\n                stream.writeInt32(pinned_msg_id);\n            }\n',
    '            if (hasFlag(flags2, FLAG_22)) {\n                stream.writeInt32(pinned_msg_id);\n            }\n'
    '            if (hasFlag(flags2, FLAG_24)) {\n                tag_perks.serializeToStream(stream);\n            }\n')
once('                case TL_channel.constructor:\n                    return new TL_channel();\n',
     '                case TL_channel.constructor:\n                case 0x7ad15240: // layer 233, before Blue Tag: the same fields without tag_perks\n                    return new TL_channel();\n')

# --- participants
for name, old_id, new_id, last in [
    ('TL_channelParticipant', '0x1BD54456', '0xB8123BC8', 'rank'),
    ('TL_channelParticipantSelf', '0xA9478A1A', '0x50CAD9EE', 'rank'),
]:
    in_class(name, 'ChannelParticipant', f'constructor = {old_id};', f'constructor = {new_id}; // Blue Tag (was {old_id})')
    in_class(name, 'ChannelParticipant',
        '            if (hasFlag(flags, FLAG_2)) {\n                rank = stream.readString(exception);\n            }\n',
        '            if (hasFlag(flags, FLAG_2)) {\n                rank = stream.readString(exception);\n            }\n'
        '            if (hasFlag(flags, FLAG_3)) {\n                tag_perks = TL_chatMemberTagPerks.TLdeserialize(stream, stream.readInt32(exception), exception);\n            }\n')
    in_class(name, 'ChannelParticipant',
        '            flags = setFlag(flags, FLAG_2, rank != null);\n',
        '            flags = setFlag(flags, FLAG_2, rank != null);\n            flags = setFlag(flags, FLAG_3, tag_perks != null);\n')
    in_class(name, 'ChannelParticipant',
        '            if (hasFlag(flags, FLAG_2)) {\n                stream.writeString(rank);\n            }\n',
        '            if (hasFlag(flags, FLAG_2)) {\n                stream.writeString(rank);\n            }\n'
        '            if (hasFlag(flags, FLAG_3)) {\n                tag_perks.serializeToStream(stream);\n            }\n')
    once(f'                case {name}.constructor:\n                    result = new {name}();\n                    break;\n',
         f'                case {name}.constructor:\n                case {old_id.lower()}: // layer 233, before Blue Tag\n                    result = new {name}();\n                    break;\n')

# --- message
in_class('TL_message', 'Message', 'constructor = 0x7600b9d3;', 'constructor = 0xb917471c; // Blue Tag (was 0x7600b9d3)')
in_class('TL_message', 'Message',
    '            paid_suggested_post_ton = hasFlag(flags2, FLAG_9);\n',
    '            paid_suggested_post_ton = hasFlag(flags2, FLAG_9);\n            from_rank_blue = hasFlag(flags2, FLAG_20);\n')
in_class('TL_message', 'Message',
    '            flags2 = setFlag(flags2, FLAG_12, from_rank != null);\n',
    '            flags2 = setFlag(flags2, FLAG_12, from_rank != null);\n            flags2 = setFlag(flags2, FLAG_20, from_rank_blue);\n')
once('                case TL_message.constructor:\n                    return new TL_message();\n',
     '                case TL_message.constructor:\n                case 0x7600b9d3: // layer 233, before Blue Tag\n                    return new TL_message();\n')

# --- admin log
once('                case TL_channelAdminLogEventActionParticipantEditRank.constructor:\n',
     '                case TL_channelAdminLogEventActionParticipantEditTagPerks.constructor:\n'
     '                    result = new TL_channelAdminLogEventActionParticipantEditTagPerks();\n                    break;\n'
     '                case TL_channelAdminLogEventActionParticipantEditRank.constructor:\n')

NEW_TYPES = '''    // Blue Tag (see SPEC.md): perks of a member tag
    public static class TL_chatMemberTagPerks extends TLObject {
        public static final int constructor = 0x78b4ccb0;

        public int flags;
        public boolean free_messages;
        public int slowmode_seconds;
        public int until_date;
        public int messages_limit;
        public int messages_used;

        public static TL_chatMemberTagPerks TLdeserialize(InputSerializedData stream, int constructor, boolean exception) {
            if (TL_chatMemberTagPerks.constructor != constructor) {
                if (exception) {
                    throw new RuntimeException(String.format("can't parse magic %x in TL_chatMemberTagPerks", constructor));
                }
                return null;
            }
            TL_chatMemberTagPerks result = new TL_chatMemberTagPerks();
            result.readParams(stream, exception);
            return result;
        }

        @Override
        public void readParams(InputSerializedData stream, boolean exception) {
            flags = stream.readInt32(exception);
            free_messages = hasFlag(flags, FLAG_0);
            if (hasFlag(flags, FLAG_1)) {
                slowmode_seconds = stream.readInt32(exception);
            }
            if (hasFlag(flags, FLAG_2)) {
                until_date = stream.readInt32(exception);
            }
            if (hasFlag(flags, FLAG_3)) {
                messages_limit = stream.readInt32(exception);
            }
            if (hasFlag(flags, FLAG_4)) {
                messages_used = stream.readInt32(exception);
            }
        }

        @Override
        public void serializeToStream(OutputSerializedData stream) {
            stream.writeInt32(constructor);
            flags = setFlag(flags, FLAG_0, free_messages);
            flags = setFlag(flags, FLAG_1, slowmode_seconds != 0);
            flags = setFlag(flags, FLAG_2, until_date != 0);
            flags = setFlag(flags, FLAG_3, messages_limit != 0);
            flags = setFlag(flags, FLAG_4, messages_used != 0);
            stream.writeInt32(flags);
            if (hasFlag(flags, FLAG_1)) {
                stream.writeInt32(slowmode_seconds);
            }
            if (hasFlag(flags, FLAG_2)) {
                stream.writeInt32(until_date);
            }
            if (hasFlag(flags, FLAG_3)) {
                stream.writeInt32(messages_limit);
            }
            if (hasFlag(flags, FLAG_4)) {
                stream.writeInt32(messages_used);
            }
        }
    }

    public static class TL_channelAdminLogEventActionParticipantEditTagPerks extends ChannelAdminLogEventAction {
        public static final int constructor = 0x4128ea6d;

        public int flags;
        public long user_id;
        public TL_chatMemberTagPerks prev_perks;
        public TL_chatMemberTagPerks new_perks;

        @Override
        public void readParams(InputSerializedData stream, boolean exception) {
            flags = stream.readInt32(exception);
            user_id = stream.readInt64(exception);
            if (hasFlag(flags, FLAG_0)) {
                prev_perks = TL_chatMemberTagPerks.TLdeserialize(stream, stream.readInt32(exception), exception);
            }
            if (hasFlag(flags, FLAG_1)) {
                new_perks = TL_chatMemberTagPerks.TLdeserialize(stream, stream.readInt32(exception), exception);
            }
        }

        @Override
        public void serializeToStream(OutputSerializedData stream) {
            stream.writeInt32(constructor);
            flags = setFlag(flags, FLAG_0, prev_perks != null);
            flags = setFlag(flags, FLAG_1, new_perks != null);
            stream.writeInt32(flags);
            stream.writeInt64(user_id);
            if (hasFlag(flags, FLAG_0)) {
                prev_perks.serializeToStream(stream);
            }
            if (hasFlag(flags, FLAG_1)) {
                new_perks.serializeToStream(stream);
            }
        }
    }

'''
once('    public static class TL_channelAdminLogEventActionParticipantEditRank extends ChannelAdminLogEventAction {',
     NEW_TYPES + '    public static class TL_channelAdminLogEventActionParticipantEditRank extends ChannelAdminLogEventAction {')

# --- method, next to messages.editChatParticipantRank
a = s.index('    public static class TL_messages_editChatParticipantRank extends TLMethod<Updates> {')
m = re.search(r'\n    public static ', s[a + 10:]); ins = a + 10 + m.start() + 1
METHOD = '''    // Blue Tag: gives a member perks, or takes them away when perks == null
    public static class TL_channels_editMemberTagPerks extends TLMethod<Updates> {
        public static final int constructor = 0x72de3d23;

        public int flags;
        public InputChannel channel;
        public InputPeer participant;
        public TL_chatMemberTagPerks perks;

        @Override
        public Updates deserializeResponseT(InputSerializedData stream, int constructor, boolean exception) {
            return Updates.TLdeserialize(stream, constructor, exception);
        }

        @Override
        public void serializeToStream(OutputSerializedData stream) {
            stream.writeInt32(constructor);
            flags = setFlag(flags, FLAG_0, perks != null);
            stream.writeInt32(flags);
            channel.serializeToStream(stream);
            participant.serializeToStream(stream);
            if (hasFlag(flags, FLAG_0)) {
                perks.serializeToStream(stream);
            }
        }
    }

'''
s = s[:ins] + METHOD + s[ins:]
open(p, 'w').write(s); print('patched', p)
