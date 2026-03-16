
import time

cooldowns = {}

def check(user_id, cooldown):
    now = time.time()

    if user_id not in cooldowns:
        cooldowns[user_id] = now
        return True

    if now - cooldowns[user_id] >= cooldown:
        cooldowns[user_id] = now
        return True

    return False
