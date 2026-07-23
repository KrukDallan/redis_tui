import redis
from typing import Dict, Any, List, Optional

class RedisDataHelper:    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.client = redis.Redis(
            host=host, 
            port=port, 
            db=db, 
            password=password, 
            decode_responses=True
        )
        self.client.config_get("notify-keyspace-events", "KEA")

    def get_all_keys_and_values(self, pattern: str = "*") -> Dict[str, Any]:
        all_data: Dict[str, Any] = {}
        
        for key in self.client.scan_iter(match=pattern):
            key_type = self.client.type(key)
            
            if key_type == "string":
                all_data[key] = self.client.get(key)
            elif key_type == "hash":
                all_data[key] = self.client.hgetall(key)
            elif key_type == "list":
                all_data[key] = self.client.lrange(key, 0, -1)
            elif key_type == "set":
                all_data[key] = self.client.smembers(key)
            elif key_type == "zset":
                all_data[key] = self.client.zrange(key, 0, -1, withscores=True)
            else:
                all_data[key] = f"<Unsupported type: {key_type}>"
        
        return dict(sorted(all_data.items(), key=lambda item: item[0]))