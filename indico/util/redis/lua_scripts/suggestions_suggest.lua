-- args=4
-- vim: ts=4 sw=4 et
local avatar = ARGV[1]
local what = ARGV[2]
local id = ARGV[3]
local score = ARGV[4]

local suggested_key = 'suggestions/suggested:'..avatar..':'..what
local ignored_key = 'suggestions/ignored:'..avatar..':'..what

if redis.call('SISMEMBER', ignored_key, id) == 0 then
    redis.call('ZADD', suggested_key, score, id)
end
