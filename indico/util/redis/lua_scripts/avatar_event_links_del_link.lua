-- args=3
-- vim: ts=4 sw=4 et
local avatar = ARGV[1]
local event = ARGV[2]
local role = ARGV[3]

local avatar_event_roles_key = 'avatar-event-links/avatar_event_roles:'..avatar..':'..event
local avatar_events_key = 'avatar-event-links/avatar_events:'..avatar
local event_avatars_key = 'avatar-event-links/event_avatars:'..event

redis.call('SREM', avatar_event_roles_key, role)
local remaining = redis.call('SCARD', avatar_event_roles_key)
if remaining == 0 then
    -- No roles remaining => avatar/event are not linked anymore
    redis.call('SREM', event_avatars_key, avatar)
    redis.call('ZREM', avatar_events_key, event)
end
