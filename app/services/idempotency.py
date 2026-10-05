async def acquire_lock(redis, key: str) -> bool:
    result = await redis.set(f"lock:{key}", "processing", nx=True, ex=300)
    return result is not None
