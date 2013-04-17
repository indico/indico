-- args=4
-- vim: ts=4 sw=4 et
local avatar = ARGV[1]
local event = ARGV[2]
local event_ts = ARGV[3]
local role = ARGV[4]

local avatar_event_roles_key = 'avatar-event-links/avatar_event_roles:'..avatar..':'..event
local avatar_events_key = 'avatar-event-links/avatar_events:'..avatar
local event_avatars_key = 'avatar-event-links/event_avatars:'..event

redis.call('SADD', event_avatars_key, avatar)
redis.call('ZADD', avatar_events_key, event_ts, event)
redis.call('SADD', avatar_event_roles_key, role)
