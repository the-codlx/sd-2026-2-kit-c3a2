# TAREFAS — C3.A2: Plataforma de IA como Serviço

## Núcleo obrigatório

- [x] 1. Autenticação JWT no Gateway.
  - Login, geração de token e proteção das rotas.
  - Testes realizados com HTTP 200 e 401.

- [x] 2. Rate limit no Gateway.
  - Controle distribuído de requisições com Redis.
  - Bloqueio validado com HTTP 429.

- [x] 3. Dockerfile de cada serviço.

- [x] 4. Docker Compose completo.
  - Execução de todos os serviços com um único comando.

- [x] 5. Deploy em nuvem.
  - Plataforma publicada no Railway.
  - Login validado com HTTP 200.
  - Consulta RAG validada com HTTP 200.
  - Indexação assíncrona validada com HTTP 202 e processada pelo worker.

- [x] 6. Resiliência.
  - Timeout, retentativas e circuit breaker.
  - Indisponibilidade e recuperação testadas localmente.

- [x] 7. Observabilidade.
  - OpenTelemetry e Jaeger.
  - Rastreamento distribuído com 16 spans e 3 serviços.
  - Evidência disponível em docs/jaeger-trace.png.

- [x] 8. HTTPS no serviço publicado.

- [x] 9. Seção de conformidade e LGPD no README.

- [x] 10. Relatório de trade-offs.
  - CAP, custo, latência e resiliência.
  - Disponível em TRADEOFFS.md.

## Extensões opcionais

- [ ] Autoescalonamento de workers.
- [ ] Componente serverless ou na borda.
- [x] Deploy automático após integração na main.
- [ ] Painel de métricas.
- [ ] Manifests de Kubernetes.

## Antes da entrega

- [x] Clonagem e execução local com Docker Compose.
- [x] Teste de autenticação JWT.
- [x] Teste de consulta RAG local.
- [x] Teste de rate limit.
- [x] Teste de circuit breaker.
- [x] Teste de recuperação após falha.
- [x] Teste de indexação assíncrona.
- [x] Validação do rastreamento no Jaeger.
- [x] URL pública acessível por HTTPS.
- [x] Validação completa da consulta RAG no Railway.
- [x] Verificação local da proteção do arquivo .env.
- [x] Revisão dos logs visíveis do Gateway, ingestão e worker.
- [ ] Revisão completa dos logs e configurações de todos os serviços.
- [x] Teste final seguindo o README atualizado.
- [x] Login, consulta RAG e indexação na instalação limpa.
- [ ] Envio do link do repositório no AVA.


## Repositório

https://github.com/the-codlx/sd-2026-2-kit-c3a2

## URL pública

https://sd-2026-2-kit-c3a2-production-bc549286.up.railway.app/docs
