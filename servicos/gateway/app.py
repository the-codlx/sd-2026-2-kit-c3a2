
"""
API Gateway - Plataforma de IA como Serviço.
Autenticação JWT, rate limit, roteamento e resiliência.
"""

import os
import time
import secrets
from datetime import datetime, timedelta, timezone

import jwt
import redis
import requests

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from pydantic import BaseModel

from servicos.comum.circuit_breaker import CircuitBreaker, CircuitoAberto


app = FastAPI(title="Gateway - C3.A2")

# Configurações
URL_GERACAO = os.environ["URL_GERACAO"]
URL_INGESTAO = os.environ["URL_INGESTAO"]
REDIS_URL = os.environ["REDIS_URL"]

JWT_SEGREDO = os.environ["JWT_SEGREDO"]
USUARIO_DEMO = os.environ["USUARIO_DEMO"]
SENHA_DEMO = os.environ["SENHA_DEMO"]

LIMITE_POR_MINUTO = int(os.getenv("LIMITE_POR_MINUTO", "30"))

cliente_redis = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_timeout=3,
    socket_connect_timeout=3
)

seguranca = HTTPBearer(auto_error=False)

# Um circuit breaker para cada serviço
disjuntor_geracao = CircuitBreaker(
    limite_falhas=3,
    espera_segundos=20
)

disjuntor_ingestao = CircuitBreaker(
    limite_falhas=3,
    espera_segundos=20
)


# Modelos de entrada
class Login(BaseModel):
    usuario: str
    senha: str


class Pergunta(BaseModel):
    pergunta: str


class Documento(BaseModel):
    texto: str
    origem: str = "desconhecida"


class Simulacao(BaseModel):
    modo: str = "nenhuma"
    falhas: int = 2


# Registro de requisições sem dados pessoais
@app.middleware("http")
async def registrar(request: Request, call_next):
    inicio = time.time()
    resposta = await call_next(request)
    ms = (time.time() - inicio) * 1000

    print(
        f"[gateway] {request.method} {request.url.path} "
        f"-> {resposta.status_code} ({ms:.1f}ms)"
    )

    return resposta


# Verificação de saúde
@app.get("/saude")
def saude():
    return {"status": "ok"}


# Autenticação JWT
@app.post("/login")
def login(dados: Login):
    usuario_valido = secrets.compare_digest(
        dados.usuario.encode(), USUARIO_DEMO.encode()
    )
    senha_valida = secrets.compare_digest(
        dados.senha.encode(), SENHA_DEMO.encode()
    )

    if not usuario_valido or not senha_valida:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha inválidos"
        )

    token = jwt.encode(
        {
            "sub": dados.usuario,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=30)
        },
        JWT_SEGREDO,
        algorithm="HS256"
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# Validação do token
def autenticar(
    credenciais: HTTPAuthorizationCredentials = Depends(seguranca)
):
    if credenciais is None:
        raise HTTPException(
            status_code=401,
            detail="Token não informado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        dados = jwt.decode(
            credenciais.credentials,
            JWT_SEGREDO,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]}
        )

        usuario = dados["sub"]

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return usuario


# Rate limit distribuído com Redis
def limitar_requisicoes(usuario: str = Depends(autenticar)):
    chave = f"gateway:rate:{usuario}"

    try:
        total = cliente_redis.eval(
            """
            local total = redis.call('INCR', KEYS[1])
            if total == 1 then
                redis.call('EXPIRE', KEYS[1], 60)
            end
            return total
            """,
            1,
            chave
        )

    except redis.RedisError:
        raise HTTPException(
            status_code=503,
            detail="Controle de requisições indisponível"
        )

    if total > LIMITE_POR_MINUTO:
        raise HTTPException(
            status_code=429,
            detail="Limite de requisições excedido"
        )

    return usuario


# Retentativas com espera progressiva
def chamar_servico(url, dados, timeout):
    max_tentativas = 3

    for tentativa in range(max_tentativas):
        try:
            resposta = requests.post(
                url,
                json=dados,
                timeout=timeout
            )

            if resposta.status_code >= 500:
                resposta.raise_for_status()

            return resposta

        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.HTTPError
        ) as erro:

            if tentativa == max_tentativas - 1:
                raise erro

            time.sleep(2 ** tentativa)


# Proxy protegido pelo circuit breaker
def encaminhar(url, dados, disjuntor, timeout=10):
    try:
        resposta = disjuntor.chamar(
            chamar_servico,
            url,
            dados,
            timeout
        )

        return Response(
            content=resposta.content,
            status_code=resposta.status_code,
            media_type=resposta.headers.get(
                "Content-Type", "application/json"
            )
        )

    except CircuitoAberto:
        raise HTTPException(
            status_code=503,
            detail="Serviço temporariamente indisponível: circuito aberto"
        )

    except requests.HTTPError as erro:
        if erro.response is not None:
            return Response(
                content=erro.response.content,
                status_code=erro.response.status_code,
                media_type=erro.response.headers.get(
                    "Content-Type", "application/json"
                )
            )

        raise HTTPException(
            status_code=503,
            detail="Serviço indisponível"
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=503,
            detail="Serviço indisponível"
        )


# Rotas protegidas
@app.post("/perguntar")
def perguntar(
    dados: Pergunta,
    usuario: str = Depends(limitar_requisicoes)
):
    return encaminhar(
        f"{URL_GERACAO}/perguntar",
        dados.model_dump(),
        disjuntor_geracao,
        timeout=35
    )


@app.post("/indexar")
def indexar(
    dados: list[Documento],
    usuario: str = Depends(limitar_requisicoes)
):
    return encaminhar(
        f"{URL_INGESTAO}/indexar",
        [documento.model_dump() for documento in dados],
        disjuntor_ingestao
    )


@app.post("/indexar-async", status_code=202)
def indexar_async(
    dados: list[Documento],
    usuario: str = Depends(limitar_requisicoes)
):
    return encaminhar(
        f"{URL_INGESTAO}/indexar-async",
        [documento.model_dump() for documento in dados],
        disjuntor_ingestao
    )


@app.post("/simulacao")
def simulacao(
    dados: Simulacao,
    usuario: str = Depends(limitar_requisicoes)
):
    return encaminhar(
        f"{URL_GERACAO}/simulacao",
        dados.model_dump(),
        disjuntor_geracao
    )
