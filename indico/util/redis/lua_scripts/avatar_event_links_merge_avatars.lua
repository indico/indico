-- args=2
-- vim: ts=4 sw=4 et
local avatar = ARGV[1]
local avatar_src = ARGV[2]

local avatar_events_key = 'avatar-event-links/avatar_events:'..avatar
local avatar_src_events_key = 'avatar-event-links/avatar_events:'..avatar_src
local event_avatars_key_prefix = 'avatar-event-links/event_avatars:'
local avatar_event_roles_key_prefix = 'avatar-event-links/avatar_event_roles:'..avatar..':'
local avatar_src_event_roles_key_prefix = 'avatar-event-links/avatar_event_roles:'..avatar_src..':'

local avatar_src_events = redis.call('ZRANGE', avatar_src_events_key, 0, -1)
for _, event in ipairs(avatar_src_events) do
    -- Remove source from all his linked events and add the target
    redis.call('SREM', event_avatars_key_prefix..event, avatar_src)
    redis.call('SADD', event_avatars_key_prefix..event, avatar)
    -- Add his roles to the target
    redis.call('SUNIONSTORE', avatar_event_roles_key_prefix..event, avatar_event_roles_key_prefix..event, avatar_src_event_roles_key_prefix..event)
    -- Delete the now unused entry
    redis.call('DEL', avatar_src_event_roles_key_prefix..event)
end

-- Merge avatar=>event mapping. Ignore source weights - they should be the same anyway.
redis.call('ZUNIONSTORE', avatar_events_key, 2, avatar_events_key, avatar_src_events_key, 'WEIGHTS', 1, 0)

-- Remove source from avatar=>event mapping
redis.call('DEL', avatar_src_events_key)
