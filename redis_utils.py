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
        
        # Iterating over keys safely using SCAN
        for key in self.client.scan_iter(match=pattern):
            key_type = self.client.type(key)
            
            # Retrieve value based on the Redis data type
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
                
        return all_data

    @staticmethod
    def compare_key_value_groups(group_a: Dict[str, Any], group_b: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Compares two key-value dictionaries and returns entries where values differ.
        
        Includes:
        - Keys present in both groups but with different values.
        - Keys that exist only in group_a or group_b.
        """
        differences = {}
        all_keys = set(group_a.keys()).union(set(group_b.keys()))

        for key in all_keys:
            val_a = group_a.get(key)
            val_b = group_b.get(key)

            if val_a != val_b:
                differences[key] = val_b

        return differences