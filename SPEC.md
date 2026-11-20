# Blue Tag — specification

A new kind of **member tag** for supergroups with paid messages.

Today a member tag can mean three things:

| Tag    | Color  | Pays for messages | Slow mode     | Admin rights |
|--------|--------|-------------------|---------------|--------------|
| Owner  | purple | no                | no            | all          |
| Admin  | green  | no                | no            | yes          |
| Member | gray   | yes               | chat-wide     | no           |
| **Blue** | **blue** | **no (optional)** | **personal** | **no**   |

A blue tag is an ordinary member tag (`rank`) plus a set of **perks** granted by an admin:

- **Free messages** — the member doesn't pay `send_paid_messages_stars`.
- **Personal slow mode** — an interval that applies to this member only and replaces the chat-wide slow mode for them (`0` = none).
- **Duration** — the perks expire at `until_date` (1 day, 7 days, or forever).
- **Message limit** — the perks expire after `messages_limit` free messages.

When the perks expire, the tag stays and turns gray again. The member pays as usual.

## API (layer 233 + Blue Tag)

The full schema is in [`api/blue_tag.tl`](api/blue_tag.tl). Constructor IDs are CRC32 values computed exactly like the official ones: `api/tl_crc32.py` reproduces `channelParticipant#1bd54456` and `messages.editChatParticipantRank#a00f32b0`.

```tl
chatMemberTagPerks#78b4ccb0 flags:# free_messages:flags.0?true slowmode_seconds:flags.1?int
    until_date:flags.2?int messages_limit:flags.3?int messages_used:flags.4?int = ChatMemberTagPerks;
```

Field changes:

| Constructor | New field | Meaning |
|---|---|---|
| `channel` | `tag_perks:flags2.24?ChatMemberTagPerks` | Perks of the **current user** in this chat, delivered like `admin_rights` and `banned_rights` |
| `channelParticipant`, `channelParticipantSelf` | `tag_perks:flags.3?ChatMemberTagPerks` | Perks of a member, for admin screens |
| `message` | `from_rank_blue:flags2.20?true` | `from_rank` is shown as a blue tag |
| `channelAdminLogEventActionParticipantEditTagPerks` | new | Recent actions entry |

Method:

```tl
channels.editMemberTagPerks#72de3d23 flags:# channel:InputChannel participant:InputPeer
    perks:flags.0?ChatMemberTagPerks = Updates;
```

- If `perks` is omitted, the perks are removed and the tag becomes gray.
- On success, the server returns `updateChannelParticipant` (with `new_participant.tag_perks`) and an updated `channel` for the target user.

Errors:

| Error | When |
|---|---|
| `CHAT_ADMIN_REQUIRED` | The caller lacks `ban_users` |
| `TAG_PERKS_RANK_EMPTY` | The member has no tag; set `rank` first with `messages.editChatParticipantRank` |
| `TAG_PERKS_PARTICIPANT_ADMIN` | The target is an admin or the owner, who are already free |
| `TAG_PERKS_INVALID` | `messages_limit` is outside 1..10000, `until_date` is in the past, or `slowmode_seconds` is not one of 0, 10, 30, 60, 300, 900, 3600 |
| `SLOWMODE_WAIT_X` | Reused for the personal slow mode on send |

## Server behaviour

1. `messages.sendMessage` (and the other send methods) from a member with active `free_messages` perks:
   - succeed without `allow_paid_stars`;
   - if `allow_paid_stars` is passed anyway, nothing is charged;
   - each sent message increments `messages_used`.
2. The personal `slowmode_seconds` replaces the chat slow mode for that member, and `SLOWMODE_WAIT_X` is returned as usual. `channelFull.slowmode_seconds` and `slowmode_next_send_date` are reported to the member with the personal values, so the existing slow-mode timers keep working.
3. The perks are inactive when `until_date <= now` or `messages_used >= messages_limit`. The server then drops them, keeps `rank`, and pushes an updated `channel` (without `tag_perks`) to the member.
4. Messages from a member with active perks carry `from_rank_blue`. Older messages keep the flag they were sent with.

## Client behaviour (implemented in every client in this repo)

1. **Edit Member Tag screen** — below the tag field, a "Blue Tag" section is shown only when:
   - the viewer can ban users;
   - the target is not an admin or the owner;
   - the chat has paid messages or slow mode.

   It contains:
   - a "Free messages" switch;
   - Slow mode: Off / 10s / 30s / 1m / 5m;
   - Duration: 1 day / 7 days / Forever;
   - Message limit: 10 / 50 / No limit.

   The preview badge turns blue. Saving calls `channels.editMemberTagPerks` after `editChatParticipantRank`.
2. **Badge** — the rank badge uses the blue peer color (index 5) when `from_rank_blue` is set, or when the member's `tag_perks` are active.
3. **Composer (member side)** — with active perks:
   - no payment confirmation and no star price on the send button;
   - the placeholder reads `Free · N left`, or `Free message` when there is no limit;
   - the personal slow mode is enforced with the standard slow-mode tooltip and timer.
4. **Counter** — the client decrements `messages_used` optimistically on send and reconciles with the next `channel` update.

## Strings (en)

```
BlueTag.Section          = "Blue Tag"
BlueTag.FreeMessages     = "Free messages"
BlueTag.FreeMessagesInfo = "%@ can write without paying Stars. Admin rights are not granted."
BlueTag.SlowMode         = "Personal slow mode"
BlueTag.Duration         = "Duration"
BlueTag.Limit            = "Message limit"
BlueTag.Day1             = "1 day"
BlueTag.Days7            = "7 days"
BlueTag.Forever          = "Forever"
BlueTag.NoLimit          = "No limit"
BlueTag.Off              = "Off"
BlueTag.PlaceholderLeft  = "Free · %@ left"
BlueTag.Placeholder      = "Free message"
BlueTag.Toast            = "Blue tag · %1$@ · %2$@"
```
