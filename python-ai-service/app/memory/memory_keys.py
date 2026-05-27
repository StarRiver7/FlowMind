PREFIX = "internsu"
SEPARATOR = ":"

def session_key(user_id, conv_id):
    return f"internsu:session:{user_id}:{conv_id}"

def state_key(user_id, conv_id):
    return f"internsu:state:{user_id}:{conv_id}"

def clarify_key(user_id, conv_id):
    return f"internsu:clarify:{user_id}:{conv_id}"

def slots_key(user_id, conv_id):
    return f"internsu:slots:{user_id}:{conv_id}"

def preference_key(user_id):
    return f"internsu:pref:{user_id}"

def conv_list_key():
    return "internsu:conv_list"

# TTL values (seconds)
TTL_SESSION = 1800      # 30 min - chat history
TTL_STATE = 900         # 15 min - agent state
TTL_CLARIFY = 900       # 15 min - clarify context
TTL_SLOTS = 900         # 15 min - collected slots
TTL_PREFERENCE = 604800 # 7 days - user preferences
TTL_CONV_LIST = 604800  # 7 days - conversation list
