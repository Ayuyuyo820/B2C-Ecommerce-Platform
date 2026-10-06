import json
from django_redis.serializers.json import JSONSerializer


class UTF8JSONSerializer(JSONSerializer):
    """让 Redis 里存中文直读（不转成 unicode 转义）的 JSON 序列化器"""
    def dumps(self, value):
        # 关键就一个参数：ensure_ascii=False，让中文原样写入而不是 \u 转义
        return json.dumps(value, cls=self.encoder_class, ensure_ascii=False).encode()