-- result=json_odict, args=3
-- vim: ts=4 sw=4 et
local avatar = ARGV[1]
local minTS = ARGV[2] ~= '' and ARGV[2] or '-inf'
local maxTS = ARGV[3] ~= '' and ARGV[3] or '+inf'

local avatar_events_key = 'avatar-event-links/avatar_events:'..avatar
local avatar_event_roles_key_prefix = 'avatar-event-links/avatar_event_roles:'..avatar..':'

local avatar_events = redis.call('ZRANGEBYSCORE', avatar_events_key, minTS, maxTS)
local res = {}
for _, event in ipairs(avatar_events) do
    table.insert(res, {event, redis.call('SMEMBERS', avatar_event_roles_key_prefix..event)})
end

return cjson.encode(res)
