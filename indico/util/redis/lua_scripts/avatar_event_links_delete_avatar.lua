-- args=1
-- vim: ts=4 sw=4 et
local avatar = ARGV[1]

local avatar_event_roles_key_prefix = 'avatar-event-links/avatar_event_roles:'..avatar..':'
local avatar_events_key = 'avatar-event-links/avatar_events:'..avatar
local event_avatars_key_prefix = 'avatar-event-links/event_avatars:'

local avatar_events = redis.call('ZRANGE', avatar_events_key, 0, -1)
for _, event in ipairs(avatar_events) do
    -- Remove avatar from linked event
    redis.call('SREM', event_avatars_key_prefix..event, avatar)
    -- Remove roles for that link
    redis.call('DEL', avatar_event_roles_key_prefix..event)
end
-- Remove event=>avatar mapping
redis.call('DEL', avatar_events_key)
