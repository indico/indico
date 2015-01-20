-- args=2
-- vim: ts=4 sw=4 et
local event = ARGV[1]
local event_ts = ARGV[2]

local event_avatars_key = 'avatar-event-links/event_avatars:'..event
local avatar_events_key_prefix = 'avatar-event-links/avatar_events:'

local event_avatars = redis.call('SMEMBERS', event_avatars_key)
for _, avatar in ipairs(event_avatars) do
    if redis.call('ZRANK', avatar_events_key_prefix..avatar, event) ~= false then
        redis.call('ZADD', avatar_events_key_prefix..avatar, event_ts, event)
    end
end
