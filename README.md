# Crypto Price Service - ETH/USDT FastAPI

KA>:>=03@C65==K9 FastAPI-A5@28A 4;O ?>;CG5=8O 40==KE ?> B>@3>2>9 ?0@5 ETH/USDT.

## "@51>20=8O

- Docker 20.10+
- Docker Compose 2.0+
- Make (>?F8>=0;L=>)
- 4GB RAM <8=8<C< 4;O 107>2>9 25@A88
- 8GB RAM 4;O 25@A88 A <>=8B>@8=3>< 8 <0AHB018@>20=85<

## KAB@K9 AB0@B

### Production @568< (<8=8<0;L=0O :>=D83C@0F8O)

```bash
# ;>=8@>20BL @5?>78B>@89
git clone <repository-url>
cd crypto-price-service

# !1>@:0 8 70?CA:
docker-compose up -d

# @>25@:0 AB0BCA0
docker-compose ps

# API 1C45B 4>ABC?5= =0 http://localhost:8000/api/
```

### Development @568<

```bash
# 0?CAB8BL 2 dev @568<5 A hot reload
docker-compose -f docker-compose.dev.yml up

# API 1C45B 4>ABC?5= =0 http://localhost:8000
```

### Production A <0AHB018@>20=85< 8 <>=8B>@8=3><

```bash
# 0?CA: A Nginx 10;0=A8@>2I8:>< (2 @5?;8:8 ?@8;>65=8O)
docker-compose -f docker-compose.scale.yml up -d

# :;NG8BL <>=8B>@8=3
docker-compose -f docker-compose.scale.yml --profile monitoring up -d

# 0AHB018@>20=85 4> 5 @5?;8:
docker-compose -f docker-compose.scale.yml up -d --scale app=5
```

## API Endpoints

- `GET /api/v1/prices/eth-usdt` - "5:CI0O F5=0 ETH/USDT
- `GET /health/liveness` - @>25@:0 687=5A?>A>1=>AB8
- `GET /health/readiness` - @>25@:0 3>B>2=>AB8
- `GET /metrics` - Prometheus <5B@8:8

## @>872>48B5;L=>ABL

8=8<0;L=0O :>=D83C@0F8O (1 :>=B59=5@, 8 2>@:5@>2) >15A?5G8205B:
- 300+ >4=>2@5<5==KE ?>4:;NG5=89
- Response time < 1000ms ?@8 ?8:>2>9 =03@C7:5
- > 500 req/s throughput

## 03@C7>G=>5 B5AB8@>20=85

```bash
# #AB0=>28BL hey
go install github.com/rakyll/hey@latest

# "5AB A 300 >4=>2@5<5==K<8 ?>4:;NG5=8O<8
hey -n 10000 -c 300 http://localhost:8000/api/v1/prices/eth-usdt

# ;8B5;L=K9 B5AB
hey -z 60s -c 300 http://localhost:8000/api/v1/prices/eth-usdt
```

## >=D83C@0F8O

A=>2=K5 ?5@5<5==K5 >:@C65=8O:

- `WORKERS` - :>;8G5AB2> Gunicorn workers (default: 8)
- `REDIS_URL` - URL 4;O ?>4:;NG5=8O : Redis
- `LOG_LEVEL` - C@>25=L ;>38@>20=8O (debug/info/warning/error)
- `CACHE_TTL` - TTL 4;O L1 :MH0 2 A5:C=40E (default: 5)

## >=8B>@8=3 (>?F8>=0;L=>)

@8 8A?>;L7>20=88 `docker-compose.scale.yml --profile monitoring`:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## Troubleshooting

### KA>:0O latency
1. @>25@8BL ;>38: `docker-compose logs app`
2. @>25@8BL CPU/Memory: `docker stats`
3. #25;8G8BL :>;8G5AB2> workers 8;8 4>1028BL @5?;8:8

### Connection refused ?@8 2KA>:>9 =03@C7:5
```bash
# #25;8G8BL ;8<8BK A8AB5<K
sudo sysctl -w net.core.somaxconn=65535
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=65535
```

### Redis connection errors
```bash
docker-compose logs redis
docker-compose restart redis
```

## @E8B5:BC@0

- Clean Architecture A @0745;5=85< =0 A;>8
- A8=E@>==0O >1@01>B:0 A AIOHTTP
- =>3>C@>2=52>5 :MH8@>20=85 (In-Memory L1 + Redis L2)
- Circuit Breaker 4;O 70I8BK >B A1>52 2=5H=8E API
- Retry <5E0=87< A exponential backoff

!<. ?>;=CN 4>:C<5=B0F8N 2 `docs/architecture.md`