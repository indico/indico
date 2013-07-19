-- args=2
-- vim: ts=4 sw=4 et
local avatar = ARGV[1]
local avatar_src = ARGV[2]

local schedule_key = 'suggestions/scheduled_checks'
local src_ignored_key_prefix = 'suggestions/ignored:'..avatar_src..':'
local dst_ignored_key_prefix = 'suggestions/ignored:'..avatar..':'
local src_suggested_key_prefix = 'suggestions/suggested:'..avatar_src..':'
local dst_suggested_key_prefix = 'suggestions/suggested:'..avatar..':'

-- Merge pending suggestion checks
if redis.call('SISMEMBER', schedule_key, avatar_src) == 1 then
    redis.call('SREM', schedule_key, avatar_src)
    redis.call('SADD', schedule_key, avatar)
end

-- Merge ignore lists
redis.call('SUNIONSTORE',
    dst_ignored_key_prefix..'category',
    dst_ignored_key_prefix..'category',
    src_ignored_key_prefix..'category'
)

-- Merge suggestions
redis.call('ZUNIONSTORE',
    dst_suggested_key_prefix..'category',
    2,
    dst_suggested_key_prefix..'category',
    src_suggested_key_prefix..'category',
    'WEIGHTS', 1, 1,
    'AGGREGATE', 'MAX'
)
