-- args=1
-- vim: ts=4 sw=4 et
local event = ARGV[1]

local avatar_event_roles_key_prefix = 'avatar-event-links/avatar_event_roles:'
local avatar_events_key_prefix = 'avatar-event-links/avatar_events:'
local event_avatars_key = 'avatar-event-links/event_avatars:'..event

local event_avatars = redis.call('SMEMBERS', event_avatars_key)
for _, avatar in ipairs(event_avatars) do
    -- Remove event from linked avatar
    redis.call('ZREM', avatar_events_key_prefix..avatar, event)
    -- Remove roles for that link
    redis.call('DEL', avatar_event_roles_key_prefix..avatar..':'..event)
end
-- Remove event=>avatar mapping
redis.call('DEL', event_avatars_key)
