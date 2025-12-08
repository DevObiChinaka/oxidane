from django.core.management.base import BaseCommand
import redis
from django.conf import settings


class Command(BaseCommand):
    help = 'Check Redis connection info and stats'

    def handle(self, *args, **options):
        try:
            # Parse Redis URL
            redis_url = settings.REDIS_URL
            self.stdout.write(f'Redis URL: {redis_url[:30]}...')
            
            # Connect to Redis
            r = redis.from_url(redis_url, decode_responses=True)
            
            # Get info
            info = r.info()
            
            self.stdout.write('\n=== Redis Server Info ===')
            self.stdout.write(f'Redis version: {info.get("redis_version")}')
            self.stdout.write(f'Uptime (days): {info.get("uptime_in_days")}')
            self.stdout.write(f'Connected clients: {info.get("connected_clients")}')
            self.stdout.write(f'Blocked clients: {info.get("blocked_clients")}')
            self.stdout.write(f'Used memory: {info.get("used_memory_human")}')
            self.stdout.write(f'Max memory: {info.get("maxmemory_human", "N/A")}')
            
            self.stdout.write('\n=== Connection Stats ===')
            self.stdout.write(f'Total connections received: {info.get("total_connections_received")}')
            self.stdout.write(f'Rejected connections: {info.get("rejected_connections")}')
            
            self.stdout.write('\n=== Current Clients ===')
            clients = r.client_list()
            self.stdout.write(f'Total active clients: {len(clients)}')
            
            for i, client in enumerate(clients, 1):
                name = client.get('name', 'unnamed')
                addr = client.get('addr', 'unknown')
                age = client.get('age', 0)
                idle = client.get('idle', 0)
                cmd = client.get('cmd', 'none')
                self.stdout.write(f'{i}. {name or "unnamed"} - {addr} - age: {age}s, idle: {idle}s, cmd: {cmd}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
